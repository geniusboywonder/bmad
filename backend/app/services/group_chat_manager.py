"""Manager for AutoGen group chats."""
from typing import List, Dict, Any
from autogen import GroupChat, GroupChatManager, ConversableAgent
import structlog

logger = structlog.get_logger(__name__)

class GroupChatManagerService:
    """Service to manage AutoGen group chats."""

    def __init__(self, llm_config: Dict[str, Any]):
        self.llm_config = llm_config

    async def run_group_chat(
        self, 
        agents: List[ConversableAgent], 
        initial_message: str
    ) -> List[Dict[str, Any]]:
        """Run a group chat with a list of agents."""

        group_chat = GroupChat(
            agents=agents,
            messages=[],
            max_round=12,
            speaker_selection_method="auto"
        )

        manager = GroupChatManager(groupchat=group_chat, llm_config=self.llm_config)

        await agents[0].a_initiate_chat(manager, message=initial_message)

        return group_chat.messages
