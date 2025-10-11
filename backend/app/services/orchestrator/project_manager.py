"""Project management service - unified lifecycle, status tracking, and performance monitoring.

This service consolidates ProjectLifecycleManager and StatusTracker to reduce over-decomposition
while maintaining clear separation of concerns. Follows targeted cleanup from Phase 3.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import structlog

from app.models.task import Task, TaskStatus
from app.models.agent import AgentStatus
from app.database.models import TaskDB, ProjectDB, AgentStatusDB
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType

logger = structlog.get_logger(__name__)

# SDLC Phases configuration
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


class ProjectManager:
    """Unified project management: lifecycle, status tracking, and performance monitoring."""

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # PROJECT LIFECYCLE MANAGEMENT
    # ========================================================================

    def create_project(self, name: str, description: str = None) -> UUID:
        """Create new project with initial state."""
        project = ProjectDB(
            name=name,
            description=description,
            status="active",
            current_phase="discovery"  # Initialize to discovery phase
        )

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        logger.info("Project created", project_id=project.id, name=name, current_phase="discovery")

        return project.id

    def list_projects(self) -> List[ProjectDB]:
        """List all projects."""
        return self.db.query(ProjectDB).all()

    def get_current_phase(self, project_id: UUID) -> str:
        """Get the current SDLC phase for a project from database."""
        project = self.db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
        if project and project.current_phase:
            return project.current_phase
        return "discovery"  # Default fallback

    def set_current_phase(self, project_id: UUID, phase: str):
        """Set the current SDLC phase for a project in database."""
        if phase not in SDLC_PHASES:
            raise ValueError(f"Invalid phase: {phase}")

        project = self.db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        project.current_phase = phase
        self.db.commit()
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
                result=db_task.output,
                created_at=db_task.created_at,
                updated_at=db_task.updated_at
            )
            tasks.append(task)

        return tasks

    def get_all_recent_tasks(self, limit: int = 50) -> List[Task]:
        """Get the most recent tasks across all projects."""
        db_tasks = self.db.query(TaskDB).order_by(TaskDB.created_at.desc()).limit(limit).all()

        tasks = []
        for db_task in db_tasks:
            task = Task(
                id=db_task.id,
                project_id=db_task.project_id,
                agent_type=db_task.agent_type,
                instructions=db_task.instructions,
                status=TaskStatus(db_task.status),
                context_ids=[UUID(cid) for cid in db_task.context_ids] if db_task.context_ids else [],
                result=db_task.output,
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
        criterion_checks = {
            "user_input_analyzed": lambda t: "analyze" in t.instructions.lower(),
            "requirements_gathered": lambda t: "requirements" in t.instructions.lower(),
            "architecture_defined": lambda t: "architecture" in t.instructions.lower(),
            "technical_plan_created": lambda t: "plan" in t.instructions.lower(),
            "api_specs_defined": lambda t: "api" in t.instructions.lower(),
            "data_models_created": lambda t: "model" in t.instructions.lower(),
            "design_reviewed": lambda t: "review" in t.instructions.lower(),
            "code_implemented": lambda t: "implement" in t.instructions.lower(),
            "unit_tests_passed": lambda t: "test" in t.instructions.lower(),
            "code_reviewed": lambda t: "review" in t.instructions.lower(),
            "tests_executed": lambda t: "test" in t.instructions.lower(),
            "quality_gates_passed": lambda t: "quality" in t.instructions.lower(),
            "performance_validated": lambda t: "performance" in t.instructions.lower(),
            "deployment_verified": lambda t: "deploy" in t.instructions.lower(),
            "production_tests_passed": lambda t: "production" in t.instructions.lower(),
            "rollback_plan_ready": lambda t: "rollback" in t.instructions.lower()
        }

        check_func = criterion_checks.get(criterion)
        if check_func:
            return any(task.status == TaskStatus.COMPLETED and check_func(task) for task in phase_tasks)

        # Default: check if any related task is completed
        return any(task.status == TaskStatus.COMPLETED for task in phase_tasks)

    # ========================================================================
    # STATUS TRACKING & PERFORMANCE MONITORING
    # ========================================================================

    def get_phase_time_analysis(self, project_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive time analysis for all project phases.

        Args:
            project_id: UUID of the project

        Returns:
            Comprehensive time analysis for all phases
        """
        current_phase = self.get_current_phase(project_id)

        phase_time_analysis = []
        total_estimated_time = 0
        total_actual_time = 0

        for phase_name, phase_config in SDLC_PHASES.items():
            phase_analysis = self._analyze_phase_time_performance(project_id, phase_name, phase_config)
            phase_time_analysis.append(phase_analysis)
            total_actual_time += phase_analysis.get("actual_duration_hours", 0)
            total_estimated_time += phase_config["estimated_duration_hours"]

        # Calculate overall metrics
        time_efficiency_percentage = (total_estimated_time / total_actual_time * 100) if total_actual_time > 0 else 0
        time_variance_percentage = ((total_actual_time - total_estimated_time) / total_estimated_time * 100) if total_estimated_time > 0 else 0

        return {
            "project_id": str(project_id),
            "current_phase": current_phase,
            "total_estimated_hours": total_estimated_time,
            "total_actual_hours": total_actual_time,
            "time_efficiency_percentage": time_efficiency_percentage,
            "time_variance_percentage": time_variance_percentage,
            "phase_time_analysis": phase_time_analysis,
            "time_based_recommendations": self._generate_time_based_recommendations(phase_time_analysis, current_phase)
        }

    def _analyze_phase_time_performance(self, project_id: UUID, phase_name: str, phase_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze time performance for a specific phase.

        Args:
            project_id: UUID of the project
            phase_name: Name of the phase
            phase_config: Phase configuration

        Returns:
            Time performance analysis for the phase
        """
        # Get tasks for this phase
        project_tasks = self.get_project_tasks(project_id)
        phase_tasks = [task for task in project_tasks if task.agent_type in phase_config["agent_sequence"]]

        # Calculate time metrics
        estimated_duration = phase_config["estimated_duration_hours"]
        max_duration = phase_config["max_duration_hours"]
        actual_duration = 0
        completed_tasks = 0
        total_tasks = len(phase_tasks)

        earliest_start = None
        latest_end = None

        for task in phase_tasks:
            if task.status == TaskStatus.COMPLETED:
                completed_tasks += 1

                # Calculate task duration
                if task.created_at and task.updated_at:
                    task_duration = (task.updated_at - task.created_at).total_seconds() / 3600  # Convert to hours
                    actual_duration += task_duration

                    # Track phase timeline
                    if not earliest_start or task.created_at < earliest_start:
                        earliest_start = task.created_at
                    if not latest_end or task.updated_at > latest_end:
                        latest_end = task.updated_at

        # Calculate performance metrics
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        efficiency_percentage = (estimated_duration / actual_duration * 100) if actual_duration > 0 else 0

        # Determine time status
        time_status = "on_track"
        if actual_duration > max_duration:
            time_status = "overtime"
        elif actual_duration > estimated_duration:
            time_status = "behind_schedule"
        elif efficiency_percentage > 120:
            time_status = "ahead_of_schedule"

        return {
            "phase": phase_name,
            "estimated_duration_hours": estimated_duration,
            "max_duration_hours": max_duration,
            "actual_duration_hours": actual_duration,
            "completion_percentage": completion_percentage,
            "efficiency_percentage": efficiency_percentage,
            "time_status": time_status,
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "phase_start": earliest_start.isoformat() if earliest_start else None,
            "phase_end": latest_end.isoformat() if latest_end else None
        }

    def _generate_time_based_recommendations(self, phase_time_analysis: List[Dict[str, Any]], current_phase: str) -> List[str]:
        """
        Generate time-based recommendations based on phase analysis.

        Args:
            phase_time_analysis: Time analysis for all phases
            current_phase: Current project phase

        Returns:
            List of recommendations
        """
        recommendations = []

        # Find current phase analysis
        current_phase_analysis = next((p for p in phase_time_analysis if p["phase"] == current_phase), None)

        if current_phase_analysis:
            if current_phase_analysis["time_status"] == "overtime":
                recommendations.append(f"Current phase ({current_phase}) is overtime. Consider escalating to HITL or simplifying scope.")
            elif current_phase_analysis["time_status"] == "behind_schedule":
                recommendations.append(f"Current phase ({current_phase}) is behind schedule. Review task complexity and resource allocation.")

        # Analyze completed phases for patterns
        overtime_phases = [p for p in phase_time_analysis if p["time_status"] == "overtime"]
        if len(overtime_phases) > 1:
            recommendations.append("Multiple phases have gone overtime. Consider revising time estimates for future projects.")

        high_efficiency_phases = [p for p in phase_time_analysis if p["efficiency_percentage"] > 120]
        if high_efficiency_phases:
            recommendations.append("Some phases completed ahead of schedule. Consider adding enhancement tasks or reducing future estimates.")

        return recommendations

    def get_time_conscious_context(self, project_id: UUID, phase: str, agent_type: str, time_budget_hours: float = None) -> Dict[str, Any]:
        """
        Get context information that is time-conscious and filtered based on current time pressure.

        Args:
            project_id: UUID of the project
            phase: Current phase
            agent_type: Type of agent requesting context
            time_budget_hours: Optional time budget for the task

        Returns:
            Time-conscious context information
        """
        # Get time analysis for current phase
        time_analysis = self.get_phase_time_analysis(project_id)
        current_phase_analysis = next(
            (p for p in time_analysis["phase_time_analysis"] if p["phase"] == phase),
            None
        )

        if not current_phase_analysis:
            return {"error": f"No time analysis available for phase {phase}"}

        # Determine time pressure level
        time_pressure = "normal"
        if current_phase_analysis["time_status"] == "overtime":
            time_pressure = "high"
        elif current_phase_analysis["time_status"] == "behind_schedule":
            time_pressure = "medium"

        # Get selective context based on time pressure
        selective_context = self.get_selective_context(project_id, phase, agent_type)

        # Apply time-based filtering
        filtered_context = self._apply_time_based_context_filtering(
            selective_context, time_pressure, agent_type
        )

        # Generate time-based instructions
        time_instructions = self._generate_time_based_instructions(
            time_pressure, time_budget_hours, agent_type, current_phase_analysis
        )

        return {
            "project_id": str(project_id),
            "phase": phase,
            "agent_type": agent_type,
            "time_pressure": time_pressure,
            "time_budget_hours": time_budget_hours,
            "context_ids": filtered_context,
            "time_instructions": time_instructions,
            "time_analysis": current_phase_analysis,
            "recommendations": self._generate_time_based_recommendations([current_phase_analysis], phase)
        }

    def _apply_time_based_context_filtering(self, context_ids: List[UUID], time_pressure: str, agent_type: str) -> List[UUID]:
        """Apply time-based filtering to context artifacts."""

        if time_pressure == "normal":
            return context_ids

        # For high time pressure, filter to most critical artifacts
        if time_pressure == "high":
            # Return only the most recent 3 artifacts (simplified filtering)
            return context_ids[-3:] if len(context_ids) > 3 else context_ids

        # For medium time pressure, filter to recent and critical artifacts
        if time_pressure == "medium":
            # Return most recent 5 artifacts
            return context_ids[-5:] if len(context_ids) > 5 else context_ids

        return context_ids

    def _generate_time_based_instructions(self, time_pressure: str, time_budget: float,
                                        agent_type: str, phase_analysis: Dict[str, Any]) -> List[str]:
        """Generate time-based instructions for agents."""

        instructions = []

        if time_pressure == "high":
            instructions.append("⚠️ HIGH TIME PRESSURE: Focus on critical tasks only. Minimize analysis depth.")
            instructions.append("Prioritize delivery over perfection. Document shortcuts taken.")

        elif time_pressure == "medium":
            instructions.append("⏰ MODERATE TIME PRESSURE: Balance quality with efficiency.")
            instructions.append("Focus on high-impact activities. Skip nice-to-have features.")

        if time_budget:
            instructions.append(f"Time budget: {time_budget} hours. Plan accordingly.")

        # Agent-specific instructions
        if agent_type == "analyst" and time_pressure != "normal":
            instructions.append("Focus on core requirements. Skip edge case analysis.")
        elif agent_type == "architect" and time_pressure != "normal":
            instructions.append("Use proven patterns. Avoid experimental architectures.")
        elif agent_type == "coder" and time_pressure != "normal":
            instructions.append("Implement MVP version. Add TODO comments for future enhancements.")

        return instructions

    def get_time_based_phase_transition(self, project_id: UUID) -> Dict[str, Any]:
        """
        Determine if phase transition should occur based on time analysis.

        Args:
            project_id: UUID of the project

        Returns:
            Time-based phase transition analysis
        """
        current_phase = self.get_current_phase(project_id)
        time_analysis = self.get_phase_time_analysis(project_id)

        current_phase_analysis = next(
            (p for p in time_analysis["phase_time_analysis"] if p["phase"] == current_phase),
            None
        )

        if not current_phase_analysis:
            return {"error": f"No analysis available for current phase {current_phase}"}

        should_transition = False
        transition_reason = ""

        # Check if phase is completed
        if current_phase_analysis["completion_percentage"] >= 100:
            should_transition = True
            transition_reason = "Phase completion criteria met"
        # Check if phase is overtime
        elif current_phase_analysis["time_status"] == "overtime":
            if current_phase_analysis["completion_percentage"] >= 80:
                should_transition = True
                transition_reason = "Phase overtime with 80%+ completion - force transition"
            else:
                remaining_time = current_phase_analysis["max_duration_hours"] - current_phase_analysis["actual_duration_hours"]
                transition_reason = f"Phase overtime with only {current_phase_analysis['completion_percentage']:.1f}% completion. {remaining_time:.1f} hours over budget."

        return {
            "project_id": str(project_id),
            "current_phase": current_phase,
            "should_transition": should_transition,
            "transition_reason": transition_reason,
            "time_analysis": current_phase_analysis,
            "recommendations": self._generate_time_based_recommendations([current_phase_analysis], current_phase)
        }

    def get_performance_metrics(self, project_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics for the project.

        Args:
            project_id: UUID of the project

        Returns:
            Performance metrics including time, quality, and efficiency metrics
        """
        # Get time analysis
        time_analysis = self.get_phase_time_analysis(project_id)

        # Get task performance metrics
        all_tasks = self.get_project_tasks(project_id)

        task_metrics = {
            "total_tasks": len(all_tasks),
            "completed_tasks": len([t for t in all_tasks if t.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in all_tasks if t.status == TaskStatus.FAILED]),
            "working_tasks": len([t for t in all_tasks if t.status == TaskStatus.WORKING]),
            "pending_tasks": len([t for t in all_tasks if t.status == TaskStatus.PENDING])
        }

        task_metrics["completion_rate"] = (task_metrics["completed_tasks"] / task_metrics["total_tasks"] * 100) if task_metrics["total_tasks"] > 0 else 0
        task_metrics["failure_rate"] = (task_metrics["failed_tasks"] / task_metrics["total_tasks"] * 100) if task_metrics["total_tasks"] > 0 else 0

        # Get agent performance
        agent_performance = self._get_agent_performance_metrics(project_id)

        return {
            "project_id": str(project_id),
            "timestamp": datetime.now().isoformat(),
            "time_metrics": {
                "total_estimated_hours": time_analysis["total_estimated_hours"],
                "total_actual_hours": time_analysis["total_actual_hours"],
                "time_efficiency_percentage": time_analysis["time_efficiency_percentage"],
                "time_variance_percentage": time_analysis["time_variance_percentage"]
            },
            "task_metrics": task_metrics,
            "agent_performance": agent_performance,
            "overall_health": self._calculate_overall_health(time_analysis, task_metrics),
            "phase_performance": time_analysis["phase_time_analysis"],
            "recommendations": time_analysis["time_based_recommendations"]
        }

    def _get_agent_performance_metrics(self, project_id: UUID) -> Dict[str, Any]:
        """Get performance metrics for each agent type."""

        all_tasks = self.get_project_tasks(project_id)
        agent_metrics = {}

        # Group tasks by agent type
        for task in all_tasks:
            agent_type = task.agent_type
            if agent_type not in agent_metrics:
                agent_metrics[agent_type] = {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "failed_tasks": 0,
                    "average_duration_hours": 0,
                    "total_duration_hours": 0
                }

            agent_metrics[agent_type]["total_tasks"] += 1

            if task.status == TaskStatus.COMPLETED:
                agent_metrics[agent_type]["completed_tasks"] += 1

                # Calculate task duration if available
                if task.created_at and task.updated_at:
                    duration = (task.updated_at - task.created_at).total_seconds() / 3600
                    agent_metrics[agent_type]["total_duration_hours"] += duration

            elif task.status == TaskStatus.FAILED:
                agent_metrics[agent_type]["failed_tasks"] += 1

        # Calculate averages and rates
        for agent_type, metrics in agent_metrics.items():
            if metrics["completed_tasks"] > 0:
                metrics["average_duration_hours"] = metrics["total_duration_hours"] / metrics["completed_tasks"]
            metrics["completion_rate"] = (metrics["completed_tasks"] / metrics["total_tasks"] * 100) if metrics["total_tasks"] > 0 else 0
            metrics["failure_rate"] = (metrics["failed_tasks"] / metrics["total_tasks"] * 100) if metrics["total_tasks"] > 0 else 0

        return agent_metrics

    def _calculate_overall_health(self, time_analysis: Dict[str, Any], task_metrics: Dict[str, Any]) -> str:
        """Calculate overall project health status."""

        # Health is based on multiple factors
        health_score = 100

        # Time performance impact
        if time_analysis["time_variance_percentage"] > 50:
            health_score -= 30
        elif time_analysis["time_variance_percentage"] > 20:
            health_score -= 15

        # Task completion impact
        if task_metrics["failure_rate"] > 20:
            health_score -= 25
        elif task_metrics["failure_rate"] > 10:
            health_score -= 10

        # Overall completion impact
        if task_metrics["completion_rate"] < 50:
            health_score -= 20
        elif task_metrics["completion_rate"] < 75:
            health_score -= 10

        # Determine health status
        if health_score >= 80:
            return "excellent"
        elif health_score >= 60:
            return "good"
        elif health_score >= 40:
            return "fair"
        elif health_score >= 20:
            return "poor"
        else:
            return "critical"

    def get_selective_context(self, project_id: UUID, phase: str, agent_type: str) -> List[UUID]:
        """
        Get selective context artifacts based on phase and agent type.

        This is a placeholder implementation - StatusTracker referenced this method
        but it wasn't defined in ProjectLifecycleManager.
        """
        # TODO: Implement actual context selection logic based on phase and agent type
        # For now, return empty list to maintain compatibility
        return []
