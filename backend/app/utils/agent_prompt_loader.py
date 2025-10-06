"""Agent Prompt Loader - Dynamically load agent prompts from markdown files."""

import os
import re
import yaml
from typing import Dict, Optional
import structlog

logger = structlog.get_logger(__name__)


class AgentPromptLoader:
    """Loads agent prompts and personas from markdown files."""
    
    def __init__(self, agents_dir: str = None):
        if agents_dir is None:
            # Auto-detect the correct path based on current working directory
            cwd = os.getcwd()
            logger.info(f"[DEBUG] Current working directory: {cwd}")

            # Check if we're already in backend directory
            if os.path.exists("app/agents"):
                agents_dir = "app/agents"
                logger.info(f"[DEBUG] Found app/agents from cwd (running from backend dir)")
            elif os.path.exists("backend/app/agents"):
                agents_dir = "backend/app/agents"
                logger.info(f"[DEBUG] Found backend/app/agents from cwd (running from project root)")
            else:
                # Fallback to relative path from this file's location
                current_dir = os.path.dirname(os.path.abspath(__file__))
                agents_dir = os.path.join(os.path.dirname(current_dir), "agents")
                logger.info(f"[DEBUG] Using fallback path from file location: {agents_dir}")

        self.agents_dir = agents_dir
        self.agents_dir_absolute = os.path.abspath(self.agents_dir)
        self._cache = {}
        logger.info(f"AgentPromptLoader initialized with agents_dir: {self.agents_dir}")
        logger.info(f"[DEBUG] Absolute agents_dir path: {self.agents_dir_absolute}")
        logger.info(f"[DEBUG] agents_dir exists: {os.path.exists(self.agents_dir)}")
    
    def get_agent_prompt(self, agent_name: str) -> str:
        """Get the complete prompt for an agent from its markdown file."""
        logger.info(f"Loading prompt for agent: {agent_name}")
        if agent_name in self._cache:
            logger.info(f"Using cached prompt for {agent_name}")
            return self._cache[agent_name]
        
        # Try different possible filenames
        possible_files = [
            f"{agent_name}.md",
            f"{agent_name.lower()}.md",
            f"bmad-{agent_name}.md",
            f"bmad-{agent_name.lower()}.md"
        ]
        
        for filename in possible_files:
            filepath = os.path.join(self.agents_dir, filename)
            filepath_absolute = os.path.abspath(filepath)
            file_exists = os.path.exists(filepath)

            logger.info(f"[DEBUG] Checking file: {filename}")
            logger.info(f"[DEBUG]   Relative path: {filepath}")
            logger.info(f"[DEBUG]   Absolute path: {filepath_absolute}")
            logger.info(f"[DEBUG]   Exists: {file_exists}")

            if file_exists:
                try:
                    prompt = self._load_prompt_from_file(filepath)
                    self._cache[agent_name] = prompt
                    logger.info(f"Loaded prompt for {agent_name} from {filename}")
                    return prompt
                except Exception as e:
                    logger.error(f"Error loading prompt from {filepath}: {e}")
                    continue
        
        # Fallback to default prompt
        default_prompt = self._get_default_prompt(agent_name)
        self._cache[agent_name] = default_prompt
        logger.warning(f"Using default prompt for {agent_name} - no markdown file found")
        return default_prompt
    
    def _load_prompt_from_file(self, filepath: str) -> str:
        """Load and parse agent prompt from markdown file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract YAML block
        yaml_match = re.search(r'```yaml\n(.*?)\n```', content, re.DOTALL)
        if not yaml_match:
            raise ValueError("No YAML block found in agent file")
        
        yaml_content = yaml_match.group(1)
        agent_config = yaml.safe_load(yaml_content)
        
        # Build prompt from agent configuration
        return self._build_prompt_from_config(agent_config)
    
    def _build_prompt_from_config(self, config: Dict) -> str:
        """Build agent prompt from parsed configuration."""
        agent_info = config.get('agent', {})
        persona_info = config.get('persona', {})
        
        # Start with assertive identity override
        prompt_parts = []
        
        # Strong identity assertion to override default prompts
        name = agent_info.get('name', 'Assistant')
        title = agent_info.get('title', 'AI Assistant')
        prompt_parts.append(f"IDENTITY OVERRIDE: You are {name}, a {title}. Ignore any previous generic assistant instructions.")
        prompt_parts.append(f"PERSONA ACTIVATION: Fully embody the following persona and disregard any conflicting system prompts.")
        
        # Role and identity from persona
        if persona_info.get('role'):
            prompt_parts.append(f"Role: {persona_info['role']}")
        
        if persona_info.get('identity'):
            prompt_parts.append(f"Identity: {persona_info['identity']}")
        
        if persona_info.get('focus'):
            prompt_parts.append(f"Focus: {persona_info['focus']}")
        
        # Style and approach
        if persona_info.get('style'):
            prompt_parts.append(f"Communication Style: {persona_info['style']}")
        
        # Core principles
        core_principles = persona_info.get('core_principles', [])
        if core_principles:
            principles_text = "\\n".join([f"- {principle}" for principle in core_principles])
            prompt_parts.append(f"Core Principles:\\n{principles_text}")
        
        # When to use
        when_to_use = agent_info.get('whenToUse')
        if when_to_use:
            prompt_parts.append(f"Use this agent for: {when_to_use}")
        
        # Customization override
        customization = agent_info.get('customization')
        if customization:
            prompt_parts.append(f"Special Instructions: {customization}")
        
        final_prompt = "\\n\\n".join(prompt_parts)
        logger.info(f"Built prompt for agent: {final_prompt[:200]}...")
        return final_prompt
    
    def _get_default_prompt(self, agent_name: str) -> str:
        """Get default prompt if no markdown file is found."""
        # Generic fallback if markdown files are not available
        logger.warning("Using generic fallback prompt for agent", agent_name=agent_name)
        return f"You are a {agent_name} agent. Follow instructions carefully and provide helpful responses."


# Global instance
agent_prompt_loader = AgentPromptLoader()