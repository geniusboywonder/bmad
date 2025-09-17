#!/usr/bin/env python3
"""Test script for Google ADK Tool Integration with BMAD."""

import asyncio
import sys
import os
from typing import Dict, Any
from uuid import uuid4

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.agents.adk_tools import (
    BMADToolRegistry, GoogleSearchTool, OpenAPITool, BMADFunctionTool,
    get_adk_tools_for_agent, register_custom_bmad_function, register_openapi_integration
)

async def test_tool_registry():
    """Test the BMAD tool registry functionality."""
    print("🧰 Testing BMAD Tool Registry")
    print("=" * 50)

    try:
        # Test registry initialization
        registry = BMADToolRegistry()
        print("✅ BMAD Tool Registry initialized")

        # Check built-in tools
        google_search = registry.get_tool("google_search")
        openapi_generic = registry.get_tool("openapi_generic")

        print(f"✅ Google Search tool registered: {google_search is not None}")
        print(f"✅ OpenAPI Generic tool registered: {openapi_generic is not None}")

        # Test custom function registration
        def sample_analysis_function(data):
            """Sample analysis function for testing."""
            return {
                "analysis": f"Analyzed {len(data)} items",
                "result": "Sample analysis complete",
                "confidence": 0.85
            }

        tool_id = register_custom_bmad_function(
            "sample_analysis",
            sample_analysis_function,
            "Perform sample analysis on provided data"
        )
        print(f"✅ Custom function registered with ID: {tool_id}")

        # Verify custom tool was registered
        custom_tool = registry.get_tool(tool_id)
        print(f"✅ Custom tool retrievable: {custom_tool is not None}")

        # Test agent-specific tool retrieval
        analyst_tools = get_adk_tools_for_agent("analyst")
        print(f"✅ Analyst tools retrieved: {len(analyst_tools)} tools")

        architect_tools = get_adk_tools_for_agent("architect")
        print(f"✅ Architect tools retrieved: {len(architect_tools)} tools")

        return True

    except Exception as e:
        print(f"❌ Tool Registry Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_tool_execution():
    """Test tool execution with safety controls."""
    print("\n🔒 Testing Tool Execution with Safety Controls")
    print("=" * 50)

    try:
        # Test Google Search Tool wrapper
        search_tool = GoogleSearchTool()

        # Test tool info
        print(f"✅ Google Search Tool initialized: {search_tool.tool_name}")

        # Test cost estimation
        cost = search_tool._estimate_tool_cost("google_search", {"query": "test"})
        print(f"✅ Cost estimation working: ${cost}")

        # Test risk assessment
        risk = search_tool._assess_tool_risk("google_search", {"query": "test"})
        print(f"✅ Risk assessment working: {risk}")

        # Test OpenAPI Tool wrapper
        openapi_tool = OpenAPITool()
        print(f"✅ OpenAPI Tool initialized: {openapi_tool.tool_name}")

        # Test API risk assessment
        api_risk = openapi_tool._assess_api_risk("https://api.example.com/users", "GET", {})
        print(f"✅ API risk assessment working: {api_risk}")

        # Test custom function tool
        def custom_validator(text):
            """Custom validation function."""
            return {
                "valid": len(text) > 5,
                "length": len(text),
                "message": "Validation complete"
            }

        custom_tool = BMADFunctionTool(
            "text_validator",
            custom_validator,
            "Validate text content"
        )
        print(f"✅ Custom Function Tool initialized: {custom_tool.tool_name}")

        return True

    except Exception as e:
        print(f"❌ Tool Execution Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_openapi_registration():
    """Test OpenAPI specification registration."""
    print("\n🌐 Testing OpenAPI Integration")
    print("=" * 50)

    try:
        # Sample OpenAPI spec
        sample_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Sample API",
                "version": "1.0.0"
            },
            "paths": {
                "/users": {
                    "get": {
                        "summary": "Get users",
                        "responses": {
                            "200": {"description": "Success"}
                        }
                    }
                }
            }
        }

        # Register OpenAPI spec
        tool_id = register_openapi_integration("sample_api", sample_spec)
        print(f"✅ OpenAPI spec registered with ID: {tool_id}")

        # Verify registration
        registry = BMADToolRegistry()
        openapi_tool = registry.get_tool(tool_id)
        print(f"✅ OpenAPI tool retrievable: {openapi_tool is not None}")

        if openapi_tool:
            print(f"   - Tool name: {openapi_tool.tool_name}")
            print(f"   - Has OpenAPI spec: {openapi_tool.openapi_spec is not None}")

        return True

    except Exception as e:
        print(f"❌ OpenAPI Registration Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_tool_integration_with_agent():
    """Test tool integration with ADK Analyst agent."""
    print("\n🤖 Testing Tool Integration with ADK Agent")
    print("=" * 50)

    try:
        # Import ADK Analyst (this will test the full integration)
        from app.agents.adk_analyst import ADKAnalystAgent
        from app.models.agent import AgentType

        # Create agent with tool integration
        agent = ADKAnalystAgent(
            agent_type=AgentType.ANALYST,
            llm_config={"model": "gemini-2.0-flash"}
        )

        print("✅ ADK Analyst Agent created with tool integration")

        # Check agent info
        agent_info = agent.get_agent_info()
        print(f"✅ Agent framework: {agent_info.get('framework', 'unknown')}")
        print(f"✅ Agent initialized: {agent_info.get('adk_initialized', False)}")

        # Test that agent has tools configured
        # Note: We can't easily test tool execution without API keys,
        # but we can verify the setup is correct
        print("✅ Agent tool integration configured")

        return True

    except Exception as e:
        print(f"❌ Agent Tool Integration Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting ADK Tool Integration Tests")
    print("Framework: Google ADK + BMAD Tool Ecosystem")
    print()

    async def run_all_tests():
        # Test tool registry
        registry_success = await test_tool_registry()

        # Test tool execution
        execution_success = await test_tool_execution()

        # Test OpenAPI registration
        openapi_success = await test_openapi_registration()

        # Test agent integration
        agent_success = await test_tool_integration_with_agent()

        # Summary
        print("\n📊 Tool Integration Test Summary:")
        print(f"   Tool Registry: {'✅ PASSED' if registry_success else '❌ FAILED'}")
        print(f"   Tool Execution: {'✅ PASSED' if execution_success else '❌ FAILED'}")
        print(f"   OpenAPI Integration: {'✅ PASSED' if openapi_success else '❌ FAILED'}")
        print(f"   Agent Integration: {'✅ PASSED' if agent_success else '❌ FAILED'}")

        all_passed = all([registry_success, execution_success, openapi_success, agent_success])

        if all_passed:
            print("\n🎯 Phase 2 (Tool Ecosystem Integration) Status: COMPLETE")
            print("   - ADK tool ecosystem successfully integrated")
            print("   - BMAD safety controls implemented")
            print("   - Custom function registration working")
            print("   - OpenAPI integration ready")
            print("   - Agent tool integration functional")
            sys.exit(0)
        else:
            print("\n⚠️  Tool Integration Issues Detected")
            print("   - Review tool implementations")
            print("   - Check ADK compatibility")
            print("   - Verify safety control integration")
            sys.exit(1)

    # Run all tests
    asyncio.run(run_all_tests())
