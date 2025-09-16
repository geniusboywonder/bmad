"""ADK Agent Handoff Service for structured multi-agent communication."""

from typing import Dict, Any, List, Optional, AsyncGenerator, Union
import structlog
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import uuid4, UUID

from app.models.task import Task
from app.models.handoff import HandoffSchema
from app.models.agent import AgentType
from app.services.adk_orchestration_service import ADKOrchestrationService
from app.services.context_store import ContextStoreService
from app.agents.bmad_adk_wrapper import BMADADKWrapper

logger = structlog.get_logger(__name__)


class ADKHandoffService:
    """Manages structured handoffs between ADK agents with context preservation and workflow continuity."""

    def __init__(self, db: Session):
        self.db = db
        self.orchestration_service = ADKOrchestrationService()
        self.context_store = ContextStoreService(db)
        self.active_handoffs: Dict[str, Dict[str, Any]] = {}
        self.handoff_count = 0

        logger.info("ADK Handoff Service initialized")

    async def create_structured_handoff(self,
                                       from_agent: BMADADKWrapper,
                                       to_agent: BMADADKWrapper,
                                       handoff_data: Dict[str, Any],
                                       project_id: Union[str, UUID],
                                       workflow_id: Optional[str] = None) -> str:
        """Create a structured handoff between ADK agents.

        Args:
            from_agent: The agent initiating the handoff
            to_agent: The agent receiving the handoff
            handoff_data: Data to be handed off including context and instructions
            project_id: Project identifier
            workflow_id: Optional workflow identifier for tracking

        Returns:
            Handoff ID for tracking
        """
        self.handoff_count += 1
        handoff_uuid = uuid4()
        handoff_id = str(handoff_uuid)

        try:
            # Validate handoff data
            self._validate_handoff_data(handoff_data)

            # Convert project_id to UUID if it's a string
            if isinstance(project_id, str):
                try:
                    project_uuid = UUID(project_id)
                except ValueError:
                    # If it's not a valid UUID string, generate a new one
                    project_uuid = uuid4()
            else:
                project_uuid = project_id

            # Convert context_ids to UUIDs
            context_uuids = []
            for context_id in handoff_data.get("context_ids", []):
                if isinstance(context_id, str):
                    try:
                        context_uuids.append(UUID(context_id))
                    except ValueError:
                        # Skip invalid UUID strings
                        continue
                else:
                    context_uuids.append(context_id)

            # Convert priority to int
            priority_map = {"low": 4, "medium": 2, "high": 1, "urgent": 0}
            priority_str = handoff_data.get("priority", "medium")
            priority_int = priority_map.get(priority_str, 2)

            # Create handoff schema
            handoff_schema = HandoffSchema(
                handoff_id=handoff_uuid,
                project_id=project_uuid,
                from_agent=from_agent.agent_type,
                to_agent=to_agent.agent_type,
                phase=handoff_data.get("phase", "general_handoff"),
                instructions=self._build_handoff_instructions(handoff_data),
                context_ids=context_uuids,
                expected_outputs=handoff_data.get("expected_outputs", []),
                priority=priority_int,
                metadata={
                    "workflow_id": workflow_id,
                    "handoff_type": "adk_structured",
                    "created_at": datetime.now().isoformat(),
                    "from_agent_name": from_agent.agent_name,
                    "to_agent_name": to_agent.agent_name
                }
            )

            # Store active handoff
            self.active_handoffs[handoff_id] = {
                "schema": handoff_schema,
                "from_agent": from_agent,
                "to_agent": to_agent,
                "status": "pending",
                "created_at": datetime.now(),
                "workflow_id": workflow_id
            }

            # Persist handoff for tracking
            await self._persist_handoff(handoff_schema)

            logger.info("ADK structured handoff created",
                       handoff_id=handoff_id,
                       from_agent=from_agent.agent_type,
                       to_agent=to_agent.agent_type,
                       project_id=project_id)

            return handoff_id

        except Exception as e:
            logger.error("Failed to create ADK handoff",
                        handoff_id=handoff_id,
                        from_agent=from_agent.agent_type,
                        to_agent=to_agent.agent_type,
                        error=str(e))
            raise

    async def execute_handoff(self, handoff_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute a structured handoff with real-time progress updates.

        Args:
            handoff_id: ID of the handoff to execute

        Yields:
            Progress updates and results from the handoff execution
        """
        if handoff_id not in self.active_handoffs:
            yield {"error": f"Handoff {handoff_id} not found"}
            return

        handoff_info = self.active_handoffs[handoff_id]
        handoff_schema = handoff_info["schema"]
        from_agent = handoff_info["from_agent"]
        to_agent = handoff_info["to_agent"]

        try:
            # Update handoff status
            handoff_info["status"] = "executing"
            await self._update_handoff_status(handoff_id, "executing")

            yield {
                "handoff_id": handoff_id,
                "status": "started",
                "from_agent": from_agent.agent_type,
                "to_agent": to_agent.agent_type,
                "phase": handoff_schema.phase,
                "timestamp": datetime.now().isoformat()
            }

            # Prepare context for the receiving agent
            context_data = await self._prepare_handoff_context(handoff_schema)

            # Execute the handoff through ADK orchestration
            workflow_id = f"handoff_workflow_{handoff_id}"
            workflow_config = {
                "max_rounds": 3,  # Limited rounds for handoff
                "speaker_selection": "round_robin",
                "allow_repeat_speaker": False
            }

            # Create a focused workflow for this handoff
            workflow_id_created = await self.orchestration_service.create_multi_agent_workflow(
                agents=[from_agent, to_agent],
                workflow_type="agent_handoff",
                project_id=handoff_schema.project_id,
                workflow_config=workflow_config
            )

            # Execute the handoff conversation
            handoff_prompt = self._create_handoff_prompt(handoff_schema, context_data)

            async for response in self.orchestration_service.execute_collaborative_analysis(
                workflow_id=workflow_id_created,
                initial_prompt=handoff_prompt,
                user_id=f"system_handoff_{handoff_id}",
                context_data=context_data
            ):
                if "error" in response:
                    yield {
                        "handoff_id": handoff_id,
                        "status": "error",
                        "error": response["error"],
                        "timestamp": datetime.now().isoformat()
                    }
                    await self._update_handoff_status(handoff_id, "failed", response["error"])
                    return

                # Enhance response with handoff metadata
                enhanced_response = response.copy()
                enhanced_response.update({
                    "handoff_id": handoff_id,
                    "handoff_phase": handoff_schema.phase,
                    "from_agent": from_agent.agent_type,
                    "to_agent": to_agent.agent_type
                })

                yield enhanced_response

                # Check if handoff is complete
                if response.get("is_final", False):
                    # Mark handoff as completed
                    handoff_info["status"] = "completed"
                    await self._update_handoff_status(handoff_id, "completed")

                    # Clean up the temporary workflow
                    await self.orchestration_service.terminate_workflow(workflow_id_created)

                    yield {
                        "handoff_id": handoff_id,
                        "status": "completed",
                        "final_response": response.get("content", ""),
                        "timestamp": datetime.now().isoformat()
                    }
                    break

        except Exception as e:
            error_msg = f"Handoff execution failed: {str(e)}"
            logger.error("ADK handoff execution failed",
                        handoff_id=handoff_id,
                        error=str(e))

            yield {
                "handoff_id": handoff_id,
                "status": "error",
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }

            await self._update_handoff_status(handoff_id, "failed", str(e))

    async def get_handoff_status(self, handoff_id: str) -> Optional[Dict[str, Any]]:
        """Get status and details of a handoff.

        Args:
            handoff_id: ID of the handoff to check

        Returns:
            Handoff status dictionary or None if not found
        """
        if handoff_id not in self.active_handoffs:
            return None

        handoff_info = self.active_handoffs[handoff_id]
        handoff_schema = handoff_info["schema"]

        return {
            "handoff_id": handoff_id,
            "status": handoff_info["status"],
            "from_agent": handoff_schema.from_agent,
            "to_agent": handoff_schema.to_agent,
            "phase": handoff_schema.phase,
            "priority": handoff_schema.priority,
            "created_at": handoff_info["created_at"].isoformat(),
            "workflow_id": handoff_info.get("workflow_id"),
            "expected_outputs": handoff_schema.expected_outputs
        }

    def list_active_handoffs(self, project_id: Optional[Union[str, UUID]] = None) -> List[str]:
        """List active handoff IDs, optionally filtered by project.

        Args:
            project_id: Optional project ID to filter by

        Returns:
            List of active handoff IDs
        """
        if project_id:
            # Convert project_id to UUID for comparison if it's a string
            if isinstance(project_id, str):
                try:
                    filter_uuid = UUID(project_id)
                except ValueError:
                    # If project_id is not a valid UUID string, compare as string representation
                    return [
                        hid for hid, info in self.active_handoffs.items()
                        if str(info["schema"].project_id) == project_id
                    ]
            else:
                filter_uuid = project_id

            return [
                hid for hid, info in self.active_handoffs.items()
                if info["schema"].project_id == filter_uuid
            ]
        return list(self.active_handoffs.keys())

    async def cancel_handoff(self, handoff_id: str) -> bool:
        """Cancel an active handoff.

        Args:
            handoff_id: ID of the handoff to cancel

        Returns:
            True if cancelled successfully, False otherwise
        """
        if handoff_id not in self.active_handoffs:
            logger.warning("Cannot cancel handoff - not found", handoff_id=handoff_id)
            return False

        try:
            handoff_info = self.active_handoffs[handoff_id]

            # Update status
            handoff_info["status"] = "cancelled"
            await self._update_handoff_status(handoff_id, "cancelled")

            # Clean up any associated workflows
            if handoff_info.get("workflow_id"):
                await self.orchestration_service.terminate_workflow(handoff_info["workflow_id"])

            # Remove from active handoffs
            del self.active_handoffs[handoff_id]

            logger.info("ADK handoff cancelled", handoff_id=handoff_id)
            return True

        except Exception as e:
            logger.error("Failed to cancel ADK handoff",
                        handoff_id=handoff_id,
                        error=str(e))
            return False

    def _validate_handoff_data(self, handoff_data: Dict[str, Any]) -> None:
        """Validate handoff data structure.

        Args:
            handoff_data: Handoff data to validate

        Raises:
            ValueError: If handoff data is invalid
        """
        required_fields = ["phase", "instructions"]
        for field in required_fields:
            if field not in handoff_data:
                raise ValueError(f"Missing required handoff field: {field}")

        if not handoff_data.get("instructions", "").strip():
            raise ValueError("Handoff instructions cannot be empty")

        # Validate priority if provided
        if "priority" in handoff_data:
            valid_priorities = ["low", "medium", "high", "urgent"]
            if handoff_data["priority"] not in valid_priorities:
                raise ValueError(f"Invalid priority: {handoff_data['priority']}. "
                               f"Must be one of: {valid_priorities}")

    def _build_handoff_instructions(self, handoff_data: Dict[str, Any]) -> str:
        """Build comprehensive handoff instructions from data.

        Args:
            handoff_data: Raw handoff data

        Returns:
            Formatted handoff instructions
        """
        base_instructions = handoff_data["instructions"]

        # Add context about expected outputs
        if handoff_data.get("expected_outputs"):
            outputs_text = "\n".join(f"- {output}" for output in handoff_data["expected_outputs"])
            base_instructions += f"\n\nExpected Outputs:\n{outputs_text}"

        # Add priority information
        priority = handoff_data.get("priority", "medium")
        if priority in ["high", "urgent"]:
            base_instructions += f"\n\n⚠️  PRIORITY: {priority.upper()} - Please address promptly."

        # Add any additional context
        if handoff_data.get("additional_context"):
            base_instructions += f"\n\nAdditional Context:\n{handoff_data['additional_context']}"

        return base_instructions

    def _create_handoff_prompt(self, handoff_schema: HandoffSchema,
                              context_data: Dict[str, Any]) -> str:
        """Create a structured prompt for handoff execution.

        Args:
            handoff_schema: The handoff schema
            context_data: Prepared context data

        Returns:
            Structured handoff prompt
        """
        prompt_parts = [
            f"🤝 AGENT HANDOFF: {handoff_schema.from_agent} → {handoff_schema.to_agent}",
            f"Phase: {handoff_schema.phase}",
            f"Priority: {handoff_schema.priority}",
            "",
            "HANDOFF INSTRUCTIONS:",
            handoff_schema.instructions,
            ""
        ]

        # Add context information
        if context_data.get("project_context"):
            prompt_parts.extend([
                "PROJECT CONTEXT:",
                context_data["project_context"],
                ""
            ])

        if context_data.get("previous_work"):
            prompt_parts.extend([
                "PREVIOUS WORK SUMMARY:",
                context_data["previous_work"],
                ""
            ])

        if context_data.get("artifacts"):
            artifacts_text = "\n".join(f"- {artifact}" for artifact in context_data["artifacts"])
            prompt_parts.extend([
                "AVAILABLE ARTIFACTS:",
                artifacts_text,
                ""
            ])

        # Add expected workflow
        prompt_parts.extend([
            "EXPECTED WORKFLOW:",
            "1. Acknowledge receipt of handoff and context",
            "2. Review and understand the instructions",
            "3. Ask clarifying questions if needed",
            "4. Provide your analysis/response",
            "5. Confirm completion of expected outputs",
            "",
            "Please proceed with this structured handoff."
        ])

        return "\n".join(prompt_parts)

    async def _prepare_handoff_context(self, handoff_schema: HandoffSchema) -> Dict[str, Any]:
        """Prepare context data for handoff execution.

        Args:
            handoff_schema: The handoff schema

        Returns:
            Prepared context data
        """
        context_data = {
            "project_id": handoff_schema.project_id,
            "handoff_id": handoff_schema.handoff_id,
            "from_agent": handoff_schema.from_agent,
            "to_agent": handoff_schema.to_agent,
            "phase": handoff_schema.phase
        }

        # Retrieve context artifacts if specified
        if handoff_schema.context_ids:
            try:
                artifacts = await self.context_store.get_artifacts_by_ids(handoff_schema.context_ids)
                context_data["artifacts"] = [
                    f"{artifact.artifact_type}: {artifact.content.get('title', 'Untitled')}"
                    for artifact in artifacts
                ]
            except Exception as e:
                logger.warning("Failed to retrieve handoff context artifacts",
                             handoff_id=handoff_schema.handoff_id,
                             error=str(e))
                context_data["artifacts"] = []

        return context_data

    async def _persist_handoff(self, handoff_schema: HandoffSchema) -> None:
        """Persist handoff for tracking and audit.

        Args:
            handoff_schema: The handoff schema to persist
        """
        try:
            # This would integrate with the persistence layer
            # For now, we'll just log it
            logger.info("Handoff persisted",
                       handoff_id=handoff_schema.handoff_id,
                       project_id=handoff_schema.project_id)
        except Exception as e:
            logger.warning("Failed to persist handoff",
                         handoff_id=handoff_schema.handoff_id,
                         error=str(e))

    async def _update_handoff_status(self, handoff_id: str, status: str,
                                   error_msg: Optional[str] = None) -> None:
        """Update handoff status.

        Args:
            handoff_id: ID of the handoff
            status: New status
            error_msg: Optional error message
        """
        try:
            # This would update the persistence layer
            logger.info("Handoff status updated",
                       handoff_id=handoff_id,
                       status=status,
                       error=error_msg)
        except Exception as e:
            logger.warning("Failed to update handoff status",
                         handoff_id=handoff_id,
                         status=status,
                         error=str(e))

    async def cleanup_completed_handoffs(self, max_age_hours: int = 24) -> int:
        """Clean up old completed handoffs.

        Args:
            max_age_hours: Maximum age in hours for cleanup

        Returns:
            Number of handoffs cleaned up
        """
        try:
            current_time = datetime.now()
            to_remove = []

            for handoff_id, handoff_info in self.active_handoffs.items():
                age_hours = (current_time - handoff_info["created_at"]).total_seconds() / 3600

                # Remove completed handoffs older than max_age_hours
                if (handoff_info["status"] in ["completed", "failed", "cancelled"]
                    and age_hours > max_age_hours):
                    to_remove.append(handoff_id)

            # Remove old handoffs
            for handoff_id in to_remove:
                del self.active_handoffs[handoff_id]

            logger.info("Handoff cleanup completed", cleaned_count=len(to_remove))
            return len(to_remove)

        except Exception as e:
            logger.error("Failed to cleanup handoffs", error=str(e))
            return 0
