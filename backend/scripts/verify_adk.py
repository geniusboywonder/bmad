#!/usr/bin/env python3
"""Verify ADK installation and basic functionality using correct API patterns."""

try:
    # Import using correct ADK API patterns
    from google.adk.agents import LlmAgent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.adk.tools import BaseTool
    print("✅ ADK core modules imported successfully")

    # Test basic agent creation with correct parameters
    agent = LlmAgent(
        name="test_agent",
        model="gemini-2.0-flash",  # Use correct model name
        instruction="You are a helpful test agent that responds clearly."  # Use 'instruction' not 'system_instruction'
    )
    print("✅ LlmAgent created successfully")

    # Test runner creation with required session service
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="test_app",
        session_service=session_service
    )
    print("✅ Runner created successfully with session service")

    print("\n🎉 ADK installation verified with correct API usage!")

except ImportError as e:
    print(f"❌ ADK import failed: {e}")
    print("Please install ADK: pip install google-adk")
except Exception as e:
    print(f"❌ ADK verification failed: {e}")
    print("This may indicate API changes in ADK. Check the implementation plan for correct usage patterns.")
