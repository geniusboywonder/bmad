"""Orchestrator service for managing agent workflows."""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
import structlog
import autogen_agentchat as autogen

from app.models.task import Task, TaskStatus
from app.models.agent import AgentType, AgentStatus
from app.models.handoff import HandoffSchema
from app.database.models import TaskDB, AgentStatusDB, ProjectDB, HitlRequestDB
from app.models.hitl import HitlStatus
from app.tasks.agent_tasks import process_agent_task
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType
from app.services.context_store import ContextStoreService

logger = structlog.get_logger(__name__)

# SDLC Process Flow as a structured dictionary
SDLC_PROCESS_FLOW = {
    "Phase 0: Discovery & Planning": [
        {"task_name": "Project Planning", "agent": AgentType.ANALYST, "input": "user_idea", "output": "project_plan.json", "hitl": True},
    ],
    "Phase 1: Plan": [
        {"task_name": "Requirements Analysis", "agent": AgentType.ANALYST, "input": "project_plan.json", "output": "software_specification.json", "hitl": True},
    ],
    "Phase 2: Design": [
        {"task_name": "Architectural Design", "agent": AgentType.ARCHITECT, "input": "software_specification.json", "output": "implementation_plan.json"},
        {"task_name": "Implementation Planning", "agent": AgentType.ARCHITECT, "input": "implementation_plan.json", "output": "implementation_plan.json"},
    ],
    "Phase 3: Build": [
        {"task_name": "Code Generation", "agent": AgentType.CODER, "input": "implementation_plan.json", "output": "source_code"},
        {"task_name": "Code Refinement", "agent": AgentType.CODER, "input": "source_code", "output": "source_code"},
    ],
    "Phase 4: Validate": [
        {"task_name": "Code Testing", "agent": AgentType.TESTER, "input": "source_code", "output": "test_results.json"},
        {"task_name": "Bug Fix", "agent": AgentType.CODER, "input": "test_results.json", "output": "source_code", "loop_until_pass": True},
    ],
    "Phase 5: Launch": [
        {"task_name": "Deployment", "agent": AgentType.DEPLOYER, "input": "source_code", "output": "deployment_log.json"},
        {"task_name": "Final Check", "agent": AgentType.DEPLOYER, "input": "deployment_log.json", "output": "project_status_completed"},
    ],
}


class OrchestratorService:
    """Service for orchestrating agent workflows."""
    
    def __init__(self, db: Session):
        self.db = db
        self.context_store = ContextStoreService(db)

    async def run_project_workflow(self, project_id: UUID, user_idea: str):
        """Runs the full SDLC workflow for a project."""
        logger.info("Starting project workflow", project_id=project_id)

        # Initial context is the user's idea
        current_context = {"user_idea": user_idea}
        context_artifact = self.context_store.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ORCHESTRATOR,
            artifact_type="user_input",
            content=current_context
        )
        last_artifact_id = context_artifact.context_id

        for phase, tasks in SDLC_PROCESS_FLOW.items():
            logger.info(f"Starting {phase}", project_id=project_id)
            for task_info in tasks:
                task_name = task_info["task_name"]
                agent_type = task_info["agent"]
                
                task = self.create_task(
                    project_id=project_id,
                    agent_type=agent_type.value,
                    instructions=f"Perform task: {task_name}",
                    context_ids=[last_artifact_id]
                )

                # Placeholder for autogen integration
                logger.info("Delegating task to AutoGen agent", task_id=task.task_id, agent=agent_type.value)
                
                # Simulate agent execution and artifact creation
                output_content = {"result": f"completed {task_name}"}
                
                output_artifact = self.context_store.create_artifact(
                    project_id=project_id,
                    source_agent=agent_type.value,
                    artifact_type="agent_output",
                    content=output_content
                )
                last_artifact_id = output_artifact.context_id
                self.update_task_status(task.task_id, TaskStatus.COMPLETED, output=output_content)

                if task_info.get("hitl"):
                    hitl_request = self.create_hitl_request(project_id, task.task_id, f"Approve {task_name}?")
                    await self.wait_for_hitl_response(hitl_request.request_id)
                    
                    updated_hitl_request = self.db.query(HitlRequestDB).filter(HitlRequestDB.id == hitl_request.request_id).first()
                    if updated_hitl_request.status == HitlStatus.REJECTED:
                        logger.warning("Workflow halted by user rejection.", project_id=project_id)
                        return

        logger.info("Project workflow completed", project_id=project_id)

    async def wait_for_hitl_response(self, request_id: UUID):
        # In a real app, this would involve waiting for an external event.
        # For this simulation, we can check the status in a loop with a timeout.
        # This is a simplified placeholder.
        pass

    def create_hitl_request(self, project_id: UUID, task_id: UUID, question: str) -> HitlRequestDB:
        """Create a new HITL request."""
        hitl_request = HitlRequestDB(
            project_id=project_id,
            task_id=task_id,
            question=question,
            status=HitlStatus.PENDING
        )
        self.db.add(hitl_request)
        self.db.commit()
        self.db.refresh(hitl_request)
        logger.info("HITL request created", hitl_request_id=hitl_request.id)
        return hitl_request

    def create_project(self, name: str, description: str = None) -> UUID:
        """Create a new project."""
        
        project = ProjectDB(
            name=name,
            description=description,
            status="active"
        )
        
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        
        logger.info("Project created", project_id=project.id, name=name)
        
        return project.id
    
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
        
        db_task = TaskDB(
            project_id=project_id,
            agent_type=agent_type,
            instructions=instructions,
            context_ids=context_ids
        )
        
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        
        task = Task(
            task_id=db_task.id,
            project_id=db_task.project_id,
            agent_type=db_task.agent_type,
            status=db_task.status,
            context_ids=db_task.context_ids,
            instructions=db_task.instructions,
            output=db_task.output,
            error_message=db_task.error_message,
            created_at=db_task.created_at,
            updated_at=db_task.updated_at,
            started_at=db_task.started_at,
            completed_at=db_task.completed_at
        )
        
        logger.info("Task created", 
                   task_id=task.task_id, 
                   agent_type=agent_type,
                   project_id=project_id)
        
        return task
    
    def submit_task(self, task: Task) -> str:
        """Submit a task to the Celery queue."""
        
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
            from datetime import datetime
            db_task.started_at = datetime.utcnow()
        
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            from datetime import datetime
            db_task.completed_at = datetime.utcnow()
        
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
    
    def get_project_tasks(self, project_id: UUID) -> List[Task]:
        """Get all tasks for a project."""
        
        db_tasks = self.db.query(TaskDB).filter(
            TaskDB.project_id == project_id
        ).all()
        
        tasks = []
        for db_task in db_tasks:
            task = Task(
                task_id=db_task.id,
                project_id=db_task.project_id,
                agent_type=db_task.agent_type,
                status=db_task.status,
                context_ids=db_task.context_ids,
                instructions=db_task.instructions,
                output=db_task.output,
                error_message=db_task.error_message,
                created_at=db_task.created_at,
                updated_at=db_task.updated_at,
                started_at=db_task.started_at,
                completed_at=db_task.completed_at
            )
            tasks.append(task)
        
        return tasks
