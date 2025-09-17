"""Agent coordination service - handles agent assignments, task distribution, and agent status management."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import structlog

from app.models.task import Task, TaskStatus
from app.models.agent import AgentType, AgentStatus
from app.database.models import TaskDB, AgentStatusDB
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType

logger = structlog.get_logger(__name__)


class AgentCoordinator:
    """Coordinates agent assignments and execution."""

    def __init__(self, db: Session):
        self.db = db

    def create_task(
        self,
        project_id: UUID,
        agent_type: str,
        instructions: str,
        context_ids: List[UUID] = None
    ) -> Task:
        """Create a new task for an agent."""

        if context_ids is None:
            context_ids = []

        # Convert UUIDs to strings for JSON serialization
        context_ids_str = [str(cid) for cid in context_ids]

        db_task = TaskDB(
            project_id=project_id,
            agent_type=agent_type,
            instructions=instructions,
            context_ids=context_ids_str
        )

        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)

        # Convert back to Task model
        task = Task(
            id=db_task.id,
            project_id=db_task.project_id,
            agent_type=db_task.agent_type,
            instructions=db_task.instructions,
            status=TaskStatus(db_task.status),
            context_ids=context_ids,
            created_at=db_task.created_at,
            updated_at=db_task.updated_at
        )

        logger.info("Task created",
                   task_id=task.task_id,
                   agent_type=agent_type,
                   project_id=project_id)

        return task

    def submit_task(self, task: Task) -> str:
        """Submit a task to the Celery queue."""

        # Import here to avoid circular import
        from app.tasks.agent_tasks import process_agent_task

        task_data = {
            "task_id": str(task.task_id),
            "project_id": str(task.project_id),
            "agent_type": task.agent_type,
            "instructions": task.instructions,
            "context_ids": [str(cid) for cid in task.context_ids]
        }

        # Submit to Celery
        celery_task = process_agent_task.delay(task_data)

        # Update task status to working
        self.update_task_status(task.task_id, TaskStatus.WORKING)

        # Update agent status
        self.update_agent_status(task.agent_type, AgentStatus.WORKING, task.task_id)

        # Emit WebSocket event
        event = WebSocketEvent(
            event_type=EventType.TASK_STARTED,
            project_id=task.project_id,
            task_id=task.task_id,
            agent_type=task.agent_type,
            data={
                "status": "working",
                "celery_task_id": celery_task.id
            }
        )

        # Note: In a real implementation, we would use asyncio to send the event
        logger.info("Task submitted to queue",
                   task_id=task.task_id,
                   celery_task_id=celery_task.id)

        return celery_task.id

    def update_task_status(
        self,
        task_id: UUID,
        status: TaskStatus,
        output: Dict[str, Any] = None,
        error_message: str = None
    ):
        """Update a task's status."""

        db_task = self.db.query(TaskDB).filter(TaskDB.id == task_id).first()

        if not db_task:
            logger.error("Task not found", task_id=task_id)
            return

        db_task.status = status

        if output is not None:
            db_task.output = output

        if error_message is not None:
            db_task.error_message = error_message

        if status == TaskStatus.WORKING and db_task.started_at is None:
                db_task.started_at = datetime.now(timezone.utc)

        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                db_task.completed_at = datetime.now(timezone.utc)

        self.db.commit()

        logger.info("Task status updated",
                   task_id=task_id,
                   status=status)

    def update_agent_status(
        self,
        agent_type: str,
        status: AgentStatus,
        current_task_id: UUID = None,
        error_message: str = None
    ):
        """Update an agent's status."""

        db_agent = self.db.query(AgentStatusDB).filter(
            AgentStatusDB.agent_type == agent_type
        ).first()

        if not db_agent:
            # Create new agent status record
            db_agent = AgentStatusDB(
                agent_type=agent_type,
                status=status,
                current_task_id=current_task_id,
                error_message=error_message
            )
            self.db.add(db_agent)
        else:
            db_agent.status = status
            db_agent.current_task_id = current_task_id
            if error_message is not None:
                db_agent.error_message = error_message

        self.db.commit()

        logger.info("Agent status updated",
                   agent_type=agent_type,
                   status=status)

    def get_agent_status(self, agent_type: str) -> Optional[AgentStatus]:
        """Get an agent's current status."""

        db_agent = self.db.query(AgentStatusDB).filter(
            AgentStatusDB.agent_type == agent_type
        ).first()

        if not db_agent:
            return None

        return db_agent.status

    def assign_agent_to_task(self, task: Task) -> Dict[str, Any]:
        """Assign appropriate agent to task based on requirements."""

        # Check if agent is available
        agent_status = self.get_agent_status(task.agent_type)

        if agent_status == AgentStatus.WORKING:
            return {
                "success": False,
                "error": f"Agent {task.agent_type} is currently busy",
                "agent_status": agent_status.value if agent_status else "unknown"
            }

        # Submit task to agent
        celery_task_id = self.submit_task(task)

        return {
            "success": True,
            "task_id": str(task.task_id),
            "agent_type": task.agent_type,
            "celery_task_id": celery_task_id,
            "status": "assigned"
        }

    def coordinate_multi_agent_workflow(self, project_id: UUID, agents_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Coordinate multiple agents for complex workflows."""

        assigned_tasks = []
        failed_assignments = []

        for agent_config in agents_config:
            try:
                # Create task for this agent
                task = self.create_task(
                    project_id=project_id,
                    agent_type=agent_config["agent_type"],
                    instructions=agent_config["instructions"],
                    context_ids=agent_config.get("context_ids", [])
                )

                # Assign agent to task
                assignment_result = self.assign_agent_to_task(task)

                if assignment_result["success"]:
                    assigned_tasks.append({
                        "task_id": str(task.task_id),
                        "agent_type": task.agent_type,
                        "celery_task_id": assignment_result["celery_task_id"]
                    })
                else:
                    failed_assignments.append({
                        "agent_type": agent_config["agent_type"],
                        "error": assignment_result["error"]
                    })

            except Exception as e:
                failed_assignments.append({
                    "agent_type": agent_config["agent_type"],
                    "error": str(e)
                })
                logger.error("Failed to assign agent",
                           agent_type=agent_config["agent_type"],
                           error=str(e))

        result = {
            "project_id": str(project_id),
            "total_agents": len(agents_config),
            "assigned_count": len(assigned_tasks),
            "failed_count": len(failed_assignments),
            "assigned_tasks": assigned_tasks,
            "failed_assignments": failed_assignments,
            "success": len(failed_assignments) == 0
        }

        logger.info("Multi-agent workflow coordination completed",
                   project_id=project_id,
                   assigned_count=len(assigned_tasks),
                   failed_count=len(failed_assignments))

        return result

    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of all available (non-working) agents."""

        # Get all agent statuses
        agent_statuses = self.db.query(AgentStatusDB).all()

        available_agents = []

        for agent_status in agent_statuses:
            if agent_status.status != AgentStatus.WORKING:
                available_agents.append({
                    "agent_type": agent_status.agent_type,
                    "status": agent_status.status.value,
                    "last_updated": agent_status.updated_at.isoformat() if agent_status.updated_at else None
                })

        # Also include standard agent types that don't have status records yet
        standard_agents = ["analyst", "architect", "coder", "tester", "deployer"]
        existing_types = {agent["agent_type"] for agent in available_agents}

        for agent_type in standard_agents:
            if agent_type not in existing_types:
                available_agents.append({
                    "agent_type": agent_type,
                    "status": "idle",
                    "last_updated": None
                })

        return available_agents

    def get_agent_workload(self) -> Dict[str, Any]:
        """Get current workload distribution across agents."""

        # Get all working agents
        working_agents = self.db.query(AgentStatusDB).filter(
            AgentStatusDB.status == AgentStatus.WORKING
        ).all()

        # Get all pending tasks by agent type
        pending_tasks = self.db.query(TaskDB).filter(
            TaskDB.status == TaskStatus.PENDING
        ).all()

        workload = {}

        # Count working tasks
        for agent in working_agents:
            workload[agent.agent_type] = {
                "working_tasks": 1,
                "pending_tasks": 0,
                "status": "working"
            }

        # Count pending tasks
        for task in pending_tasks:
            if task.agent_type not in workload:
                workload[task.agent_type] = {
                    "working_tasks": 0,
                    "pending_tasks": 0,
                    "status": "idle"
                }
            workload[task.agent_type]["pending_tasks"] += 1

        return workload

    def reassign_failed_task(self, task_id: UUID) -> Dict[str, Any]:
        """Reassign a failed task to the same or different agent."""

        # Get the failed task
        db_task = self.db.query(TaskDB).filter(TaskDB.id == task_id).first()

        if not db_task:
            return {"success": False, "error": "Task not found"}

        if db_task.status != TaskStatus.FAILED:
            return {"success": False, "error": "Task is not in failed state"}

        # Reset task status to pending
        db_task.status = TaskStatus.PENDING
        db_task.error_message = None
        db_task.started_at = None
        db_task.completed_at = None
        self.db.commit()

        # Create Task object and reassign
        task = Task(
            id=db_task.id,
            project_id=db_task.project_id,
            agent_type=db_task.agent_type,
            instructions=db_task.instructions,
            status=TaskStatus.PENDING,
            context_ids=[UUID(cid) for cid in db_task.context_ids] if db_task.context_ids else [],
            created_at=db_task.created_at,
            updated_at=db_task.updated_at
        )

        # Assign to agent
        assignment_result = self.assign_agent_to_task(task)

        logger.info("Task reassigned",
                   task_id=task_id,
                   success=assignment_result["success"])

        return assignment_result