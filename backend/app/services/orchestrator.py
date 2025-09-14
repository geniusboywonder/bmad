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
from app.services.autogen_service import AutoGenService

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
        self.autogen_service = AutoGenService()

    async def run_project_workflow(self, project_id: UUID, user_idea: str):
        """Runs the full SDLC workflow for a project using HandoffSchema."""
        logger.info("Starting project workflow", project_id=project_id)

        # Initial context is the user's idea
        current_context = {"user_idea": user_idea}
        context_artifact = self.context_store.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ORCHESTRATOR.value,
            artifact_type="user_input",
            content=current_context
        )
        last_artifact_id = context_artifact.context_id
        previous_agent = AgentType.ORCHESTRATOR.value

        for phase, tasks in SDLC_PROCESS_FLOW.items():
            logger.info(f"Starting {phase}", project_id=project_id)
            for task_info in tasks:
                task_name = task_info["task_name"]
                agent_type = task_info["agent"]
                
                # Create HandoffSchema for structured agent communication
                handoff = HandoffSchema(
                    handoff_id=uuid4(),
                    from_agent=previous_agent,
                    to_agent=agent_type.value,
                    project_id=project_id,
                    phase=phase,
                    context_ids=[last_artifact_id],
                    instructions=f"Execute {task_name}. Expected input: {task_info.get('input', 'previous_output')}. Expected output: {task_info.get('output', 'task_result')}.",
                    expected_outputs=[task_info.get('output', 'task_result')],
                    priority=1
                )
                
                task = self.create_task_from_handoff(handoff)
                
                # Process the task through AutoGen
                task_result = await self.process_task_with_autogen(task, handoff)
                
                # Create output artifact
                output_artifact = self.context_store.create_artifact(
                    project_id=project_id,
                    source_agent=agent_type.value,
                    artifact_type=task_info.get('output', 'agent_output'),
                    content=task_result
                )
                last_artifact_id = output_artifact.context_id
                previous_agent = agent_type.value
                
                self.update_task_status(task.task_id, TaskStatus.COMPLETED, output=task_result)

                # Handle HITL checkpoint if required
                if task_info.get("hitl"):
                    hitl_response = await self.handle_hitl_checkpoint(
                        project_id, 
                        task.task_id, 
                        f"Review and approve {task_name}",
                        task_result
                    )
                    
                    if hitl_response == "rejected":
                        logger.warning("Workflow halted by user rejection", project_id=project_id)
                        return
                    elif hitl_response == "amended":
                        # Re-process task with amended input
                        amended_artifact = self.get_latest_amended_artifact(project_id, task.task_id)
                        if amended_artifact:
                            last_artifact_id = amended_artifact.context_id

        logger.info("Project workflow completed", project_id=project_id)

    async def wait_for_hitl_response(self, request_id: UUID):
        # In a real app, this would involve waiting for an external event.
        # For this simulation, we can check the status in a loop with a timeout.
        # This is a simplified placeholder.
        pass

    def create_hitl_request(
        self,
        project_id: UUID,
        task_id: UUID,
        question: str,
        options: Optional[List[str]] = None,
        ttl_hours: Optional[int] = None
    ) -> HitlRequestDB:
        """Create a new HITL request with optional TTL."""

        # Validation
        if not question or question.strip() == "":
            raise ValueError("Question cannot be empty")

        # Validate that task belongs to the specified project
        task = self.db.query(TaskDB).filter(TaskDB.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.project_id != project_id:
            raise ValueError(f"Task {task_id} does not belong to project {project_id}")

        if options is None:
            options = []
            
        # Calculate expiration time if TTL is provided
        expires_at = None
        expiration_time = None
        if ttl_hours is not None:
            from datetime import datetime, timedelta
            expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
            expiration_time = expires_at
        
        hitl_request = HitlRequestDB(
            project_id=project_id,
            task_id=task_id,
            question=question,
            options=options,
            status=HitlStatus.PENDING,
            expires_at=expires_at,
            expiration_time=expiration_time
        )
        self.db.add(hitl_request)
        self.db.commit()
        self.db.refresh(hitl_request)
        logger.info("HITL request created", hitl_request_id=hitl_request.id, ttl_hours=ttl_hours)
        return hitl_request
    
    def process_hitl_response(
        self,
        hitl_request_id: UUID,
        action: str,
        comment: Optional[str] = None,
        amended_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a HITL response (approve, reject, or amend)."""
        
        # Get the HITL request
        hitl_request = self.db.query(HitlRequestDB).filter(
            HitlRequestDB.id == hitl_request_id
        ).first()
        
        if not hitl_request:
            raise ValueError(f"HITL request {hitl_request_id} not found")
        
        if hitl_request.status != HitlStatus.PENDING:
            raise ValueError(f"HITL request {hitl_request_id} is not in pending status")
        
        from datetime import datetime
        
        # Update the request based on action
        response_data = {"action": action, "workflow_resumed": True}
        
        if action == "approve":
            hitl_request.status = HitlStatus.APPROVED
            hitl_request.user_response = "approved"
            
        elif action == "reject":
            hitl_request.status = HitlStatus.REJECTED
            hitl_request.user_response = "rejected"
            
        elif action == "amend":
            hitl_request.status = HitlStatus.AMENDED
            hitl_request.user_response = "amended"
            if amended_data:
                hitl_request.amended_content = amended_data
                
        else:
            raise ValueError(f"Invalid action: {action}")
        
        # Common updates
        hitl_request.response_comment = comment
        hitl_request.responded_at = datetime.utcnow()
        
        # Add to history
        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user_id": user_id,
            "comment": comment,
            "amended_data": amended_data
        }
        
        if hitl_request.history is None:
            hitl_request.history = []
        hitl_request.history.append(history_entry)
        
        self.db.commit()
        self.db.refresh(hitl_request)
        
        logger.info("HITL response processed", 
                   hitl_request_id=hitl_request_id,
                   action=action,
                   new_status=hitl_request.status)
        
        return response_data

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
        
        # Convert context_ids back to UUIDs for the Pydantic model
        context_ids_uuid = [UUID(cid) if isinstance(cid, str) else cid for cid in db_task.context_ids]
        
        task = Task(
            task_id=db_task.id,
            project_id=db_task.project_id,
            agent_type=db_task.agent_type,
            status=db_task.status,
            context_ids=context_ids_uuid,
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
            # Convert context_ids back to UUIDs for the Pydantic model
            context_ids_uuid = [UUID(cid) if isinstance(cid, str) else cid for cid in db_task.context_ids]
            
            task = Task(
                task_id=db_task.id,
                project_id=db_task.project_id,
                agent_type=db_task.agent_type,
                status=db_task.status,
                context_ids=context_ids_uuid,
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
    
    def create_task_from_handoff(
        self, 
        handoff: HandoffSchema = None,
        project_id: UUID = None, 
        handoff_schema: Dict[str, Any] = None
    ) -> Task:
        """Create a task from a HandoffSchema or raw handoff data."""
        
        if handoff is not None:
            # Original interface - HandoffSchema object
            task = self.create_task(
                project_id=handoff.project_id,
                agent_type=handoff.to_agent,
                instructions=handoff.instructions,
                context_ids=handoff.context_ids
            )
        elif project_id is not None and handoff_schema is not None:
            # New interface - raw dictionary data
            from uuid import UUID as UUID_type
            context_ids_uuid = []
            if handoff_schema.get("context_ids"):
                context_ids_uuid = [
                    UUID_type(cid) if isinstance(cid, str) else cid 
                    for cid in handoff_schema["context_ids"]
                ]
            
            task = self.create_task(
                project_id=project_id,
                agent_type=handoff_schema["to_agent"],
                instructions=handoff_schema.get("task_instructions", handoff_schema.get("instructions", "")),
                context_ids=context_ids_uuid
            )
        else:
            raise ValueError("Either handoff object or (project_id, handoff_schema) must be provided")
        
        # Store the handoff metadata with the task - ensure all data is JSON serializable
        if handoff is not None:
            handoff_metadata = {
                "handoff_id": str(handoff.handoff_id),
                "from_agent": handoff.from_agent,
                "phase": handoff.phase,
                "expected_outputs": handoff.expected_outputs,
                "metadata": handoff.metadata
            }
            
            self.update_task_status(
                task.task_id, 
                TaskStatus.PENDING, 
                output=handoff_metadata
            )
            
            logger.info("Task created from handoff",
                       task_id=task.task_id,
                       handoff_id=handoff.handoff_id,
                       from_agent=handoff.from_agent,
                       to_agent=handoff.to_agent)
        else:
            # For raw handoff schema, store what we have
            handoff_metadata = {
                "handoff_source": "raw_schema",
                "from_agent": handoff_schema.get("from_agent"),
                "to_agent": handoff_schema.get("to_agent"),
                "expected_output": handoff_schema.get("expected_output"),
                "metadata": handoff_schema
            }
            
            self.update_task_status(
                task.task_id, 
                TaskStatus.PENDING, 
                output=handoff_metadata
            )
            
            logger.info("Task created from raw handoff schema",
                       task_id=task.task_id,
                       from_agent=handoff_schema.get("from_agent"),
                       to_agent=handoff_schema.get("to_agent"))
        
        return task
    
    async def process_task_with_autogen(self, task: Task, handoff: HandoffSchema) -> dict:
        """Process a task using the AutoGen framework."""
        
        # Get context artifacts for the task
        context_artifacts = self.context_store.get_artifacts_by_ids(task.context_ids)
        
        # Update agent status to working
        self.update_agent_status(task.agent_type, AgentStatus.WORKING, task.task_id)
        
        logger.info("Processing task with AutoGen", 
                   task_id=task.task_id, 
                   agent_type=task.agent_type)
        
        # Execute the task using AutoGen service
        result = await self.autogen_service.execute_task(task, handoff, context_artifacts)
        
        # Update agent status based on result
        if result.get("success", True):
            self.update_agent_status(task.agent_type, AgentStatus.IDLE)
        else:
            self.update_agent_status(task.agent_type, AgentStatus.ERROR, error_message=result.get("error"))
        
        return result
    
    async def handle_hitl_checkpoint(self, project_id: UUID, task_id: UUID, question: str, task_result: dict) -> str:
        """Handle a Human-in-the-Loop checkpoint."""
        
        hitl_request = self.create_hitl_request(project_id, task_id, question)
        
        # Add task result to HITL request for user review
        self.update_hitl_request_content(hitl_request.id, task_result)
        
        # Emit WebSocket event for real-time notification
        await self.notify_hitl_request_created(hitl_request.id)
        
        # Wait for user response (in real implementation, this would be event-driven)
        response = await self.wait_for_hitl_response(hitl_request.id)
        
        return response
    
    def update_hitl_request_content(self, request_id: UUID, content: dict):
        """Update HITL request with content for user review."""
        
        hitl_request = self.db.query(HitlRequestDB).filter(HitlRequestDB.id == request_id).first()
        if hitl_request:
            hitl_request.amended_content = content
            self.db.commit()
    
    async def notify_hitl_request_created(self, request_id: UUID):
        """Notify frontend of new HITL request via WebSocket."""
        
        event = WebSocketEvent(
            event_type=EventType.HITL_REQUEST_CREATED,
            data={"hitl_request_id": str(request_id)}
        )
        
        # In a full implementation, this would emit the event to connected WebSocket clients
        logger.info("HITL request notification sent", request_id=request_id)
    
    def get_latest_amended_artifact(self, project_id: UUID, task_id: UUID) -> Optional['ContextArtifact']:
        """Get the latest amended artifact for a task."""
        
        hitl_request = self.db.query(HitlRequestDB).filter(
            HitlRequestDB.task_id == task_id,
            HitlRequestDB.status == HitlStatus.AMENDED
        ).first()
        
        if hitl_request and hitl_request.amended_content:
            # Create new context artifact with amended content
            amended_artifact = self.context_store.create_artifact(
                project_id=project_id,
                source_agent="user_amendment",
                artifact_type="hitl_response",
                content=hitl_request.amended_content
            )
            return amended_artifact
        
        return None
    
    async def resume_workflow_after_hitl(self, hitl_request_id: UUID, hitl_action):
        """Resume workflow after HITL response."""

        logger.info("Resuming workflow after HITL response",
                   hitl_request_id=hitl_request_id,
                   hitl_action=hitl_action)

        # Get the HITL request to find the associated task and project
        hitl_request = self.db.query(HitlRequestDB).filter(
            HitlRequestDB.id == hitl_request_id
        ).first()

        if not hitl_request:
            logger.error("HITL request not found", hitl_request_id=hitl_request_id)
            return {
                "workflow_resumed": False,
                "error": "HITL request not found"
            }

        # Get the task that was waiting for HITL
        task = self.db.query(TaskDB).filter(TaskDB.id == hitl_request.task_id).first()
        if not task:
            logger.error("Task not found for HITL resume", task_id=hitl_request.task_id)
            return {
                "workflow_resumed": False,
                "error": "Associated task not found"
            }

        # Update agent status to idle (ready for next task)
        self.update_agent_status(task.agent_type, AgentStatus.IDLE)

        # Determine next action based on HITL action
        next_action = "continue_task"
        if hitl_action == "reject":
            next_action = "handle_rejection"
        elif hitl_action == "amend":
            next_action = "apply_amendments"

        # Emit workflow resume event
        event = WebSocketEvent(
            event_type=EventType.WORKFLOW_RESUMED,
            project_id=hitl_request.project_id,
            task_id=hitl_request.task_id,
            data={
                "message": "Workflow resumed after HITL response",
                "task_id": str(hitl_request.task_id),
                "agent_type": task.agent_type,
                "hitl_action": hitl_action,
                "next_action": next_action
            }
        )

        logger.info("Workflow resume event emitted",
                   project_id=hitl_request.project_id,
                   task_id=hitl_request.task_id,
                   hitl_action=hitl_action)

        return {
            "workflow_resumed": True,
            "next_action": next_action,
            "project_id": str(hitl_request.project_id),
            "task_id": str(hitl_request.task_id),
            "hitl_action": hitl_action
        }
