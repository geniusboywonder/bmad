⏺ 🏗️ Detailed Implementation Plan: ADK Feature Completion

  Based on my architectural analysis, here's a comprehensive implementation plan for the remaining ADK features:

  ---
  📋 Implementation Plan Overview

  Phase Structure

  - Phase 1: Agent Factory Integration (1-2 weeks)
  - Phase 2: Multi-Agent Orchestration (2-3 weeks)
  - Phase 3: Advanced Tool Integration (2-3 weeks)

  Total Timeline: 5-8 weeks

  Risk Level: MEDIUM

  Dependencies: Production ADK deployment, API keys configured

  ---
  Phase 1: Agent Factory Integration 🏭

  Objective: Enable seamless ADK agent creation through existing BMAD factory patterns

  1.1 Update Agent Factory Architecture

  File: backend/app/agents/agent_factory.py

  # Enhanced Agent Factory with ADK Integration
  from typing import Dict, Any, Optional
  from app.agents.bmad_adk_wrapper import BMADADKWrapper
  from app.agents.base_agent import BaseAgent

  class AgentFactory:
      """Enhanced factory supporting both legacy and ADK agents."""

      def __init__(self):
          self.adk_agent_types = {
              "analyst": {
                  "model": "gemini-2.0-flash",
                  "instruction": self._get_analyst_instruction(),
                  "tools": []
              },
              "architect": {
                  "model": "gemini-2.0-flash",
                  "instruction": self._get_architect_instruction(),
                  "tools": []
              },
              "coder": {
                  "model": "gemini-2.0-flash",
                  "instruction": self._get_coder_instruction(),
                  "tools": self._get_coder_tools()
              }
          }

      async def create_agent(self, agent_type: str, agent_id: str,
                            config: Dict[str, Any]) -> BaseAgent:
          """Create agent with ADK support."""

          # Check ADK feature flag
          use_adk = config.get("use_adk", False)

          if use_adk and agent_type in self.adk_agent_types:
              return await self._create_adk_agent(agent_type, agent_id, config)
          else:
              # Fallback to legacy agents
              return self._create_legacy_agent(agent_type, agent_id, config)

      async def _create_adk_agent(self, agent_type: str, agent_id: str,
                                 config: Dict[str, Any]) -> BMADADKWrapper:
          """Create ADK-based agent."""
          adk_config = self.adk_agent_types[agent_type]

          # Override with user config
          model = config.get("model", adk_config["model"])
          instruction = config.get("instruction", adk_config["instruction"])
          tools = config.get("tools", adk_config["tools"])

          wrapper = BMADADKWrapper(
              agent_name=f"{agent_type}_{agent_id}",
              agent_type=agent_type,
              model=model,
              instruction=instruction,
              tools=tools
          )

          # Initialize the wrapper
          await wrapper.initialize()
          return wrapper

  1.2 Configuration Management

  File: backend/app/config/agent_configs.py

  # Agent Configuration with ADK Feature Flags
  AGENT_CONFIGS = {
      "analyst": {
          "use_adk": True,  # Enable ADK for analysts first
          "model": "gemini-2.0-flash",
          "fallback_to_legacy": True,
          "rollout_percentage": 25  # Gradual rollout
      },
      "architect": {
          "use_adk": False,  # Enable after analyst validation
          "rollout_percentage": 0
      },
      "coder": {
          "use_adk": False,
          "rollout_percentage": 0
      }
  }

  class ADKRolloutManager:
      """Manages gradual ADK rollout."""

      def should_use_adk(self, agent_type: str, user_id: str) -> bool:
          """Determine if ADK should be used based on rollout percentage."""
          config = AGENT_CONFIGS.get(agent_type, {})

          if not config.get("use_adk", False):
              return False

          rollout_pct = config.get("rollout_percentage", 0)
          user_hash = hash(user_id) % 100

          return user_hash < rollout_pct

  1.3 Integration Testing

  File: backend/tests/test_agent_factory_adk.py

  import pytest
  from app.agents.agent_factory import AgentFactory
  from app.agents.bmad_adk_wrapper import BMADADKWrapper

  @pytest.mark.asyncio
  async def test_adk_agent_creation():
      """Test ADK agent creation through factory."""
      factory = AgentFactory()

      config = {"use_adk": True}
      agent = await factory.create_agent("analyst", "test_001", config)

      assert isinstance(agent, BMADADKWrapper)
      assert agent.agent_type == "analyst"
      assert agent.is_initialized

  @pytest.mark.asyncio
  async def test_legacy_fallback():
      """Test fallback to legacy agents."""
      factory = AgentFactory()

      config = {"use_adk": False}
      agent = await factory.create_agent("analyst", "test_002", config)

      # Should create legacy agent (not BMADADKWrapper)
      assert not isinstance(agent, BMADADKWrapper)

  Phase 1 Success Criteria

  - Agent factory creates ADK agents when use_adk: true
  - Gradual rollout system controls ADK adoption rate
  - Legacy agents remain functional as fallback
  - Configuration management enables feature flags
  - Integration tests validate factory behavior

  ---
  Phase 2: Multi-Agent Orchestration 🤝

  Objective: Enable complex multi-agent workflows using ADK's GroupChatManager

  2.1 GroupChat Integration

  File: backend/app/services/adk_orchestration_service.py

  from typing import List, Dict, Any, AsyncGenerator
  from google.adk.agents import LlmAgent
  from google.adk.runners import GroupChatManager, GroupChat
  from google.adk.sessions import InMemorySessionService
  from google.genai import types
  import structlog

  logger = structlog.get_logger(__name__)

  class ADKOrchestrationService:
      """Multi-agent orchestration using ADK GroupChat."""

      def __init__(self):
          self.session_service = InMemorySessionService()
          self.active_group_chats: Dict[str, GroupChatManager] = {}

      async def create_multi_agent_workflow(self,
                                           agents: List[BMADADKWrapper],
                                           workflow_type: str,
                                           project_id: str) -> str:
          """Create multi-agent collaborative workflow."""

          # Extract ADK agents from wrappers
          adk_agents = [wrapper.adk_agent for wrapper in agents]

          # Create GroupChat configuration
          group_chat = GroupChat(
              agents=adk_agents,
              max_rounds=10,
              speaker_selection_method="auto"  # Let ADK decide speaker order
          )

          # Create GroupChatManager
          manager = GroupChatManager(
              group_chat=group_chat,
              session_service=self.session_service
          )

          # Generate workflow ID
          workflow_id = f"workflow_{project_id}_{workflow_type}_{len(self.active_group_chats)}"
          self.active_group_chats[workflow_id] = manager

          logger.info("Multi-agent workflow created",
                     workflow_id=workflow_id,
                     agent_count=len(agents))

          return workflow_id

      async def execute_collaborative_analysis(self,
                                             workflow_id: str,
                                             initial_prompt: str,
                                             user_id: str) -> AsyncGenerator[Dict[str, Any], None]:
          """Execute collaborative analysis workflow."""

          if workflow_id not in self.active_group_chats:
              yield {"error": f"Workflow {workflow_id} not found"}
              return

          manager = self.active_group_chats[workflow_id]

          # Create session
          session_id = f"session_{workflow_id}_{user_id}"
          session = await self.session_service.create_session(
              app_name="bmad_orchestration",
              user_id=user_id,
              session_id=session_id
          )

          # Create initial message
          content = types.Content(
              role='user',
              parts=[types.Part(text=initial_prompt)]
          )

          try:
              # Execute group chat
              async for event in manager.run_async(
                  user_id=user_id,
                  session_id=session_id,
                  new_message=content
              ):
                  if event.content and event.content.parts:
                      yield {
                          "agent": event.agent_name if hasattr(event, 'agent_name') else "unknown",
                          "content": event.content.parts[0].text,
                          "timestamp": event.timestamp if hasattr(event, 'timestamp') else None,
                          "is_final": event.is_final_response()
                      }

          except Exception as e:
              logger.error("Group chat execution failed",
                          workflow_id=workflow_id, error=str(e))
              yield {"error": f"Workflow execution failed: {str(e)}"}

  2.2 Workflow Templates

  File: backend/app/workflows/adk_workflow_templates.py

  from typing import Dict, List, Any
  from dataclasses import dataclass

  @dataclass
  class WorkflowStep:
      agent_type: str
      instruction: str
      expected_output: str
      handoff_conditions: List[str]

  class ADKWorkflowTemplates:
      """Predefined multi-agent workflow templates."""

      COMPREHENSIVE_ANALYSIS = [
          WorkflowStep(
              agent_type="analyst",
              instruction="Analyze the requirements and create a detailed PRD",
              expected_output="product_requirements_document",
              handoff_conditions=["prd_complete", "requirements_clear"]
          ),
          WorkflowStep(
              agent_type="architect",
              instruction="Design system architecture based on the PRD",
              expected_output="system_architecture",
              handoff_conditions=["architecture_complete", "technical_feasible"]
          ),
          WorkflowStep(
              agent_type="coder",
              instruction="Implement core functionality based on architecture",
              expected_output="source_code",
              handoff_conditions=["core_features_implemented"]
          )
      ]

      REQUIREMENTS_REFINEMENT = [
          WorkflowStep(
              agent_type="analyst",
              instruction="Initial requirements analysis",
              expected_output="initial_analysis",
              handoff_conditions=["analysis_complete"]
          ),
          WorkflowStep(
              agent_type="architect",
              instruction="Technical feasibility review and feedback",
              expected_output="feasibility_review",
              handoff_conditions=["technical_review_complete"]
          ),
          WorkflowStep(
              agent_type="analyst",
              instruction="Refine requirements based on technical feedback",
              expected_output="refined_requirements",
              handoff_conditions=["requirements_refined"]
          )
      ]

  2.3 Agent Handoff System

  File: backend/app/services/adk_handoff_service.py

  from typing import Dict, Any, Optional
  from app.models.task import Task
  from app.services.adk_orchestration_service import ADKOrchestrationService

  class ADKHandoffService:
      """Manages structured handoffs between ADK agents."""

      def __init__(self):
          self.orchestration_service = ADKOrchestrationService()

      async def create_handoff_task(self,
                                   from_agent: str,
                                   to_agent: str,
                                   handoff_data: Dict[str, Any],
                                   project_id: str) -> Task:
          """Create structured handoff task between agents."""

          handoff_instruction = self._build_handoff_instruction(
              from_agent, to_agent, handoff_data
          )

          task = Task(
              project_id=project_id,
              agent_type=to_agent,
              instructions=handoff_instruction,
              context_ids=handoff_data.get("context_ids", []),
              metadata={
                  "handoff_type": "adk_structured_handoff",
                  "from_agent": from_agent,
                  "handoff_data": handoff_data
              }
          )

          return task

      def _build_handoff_instruction(self,
                                    from_agent: str,
                                    to_agent: str,
                                    handoff_data: Dict[str, Any]) -> str:
          """Build structured handoff instruction."""

          instruction_template = f"""
          AGENT HANDOFF: {from_agent} → {to_agent}

          Previous Work Summary:
          {handoff_data.get('work_summary', 'No summary provided')}

          Handoff Context:
          {handoff_data.get('context', 'No context provided')}

          Your Task:
          {handoff_data.get('next_task', 'Continue the workflow')}

          Expected Output:
          {handoff_data.get('expected_output', 'Complete the assigned work')}

          Success Criteria:
          {handoff_data.get('success_criteria', 'Meet quality standards')}
          """

          return instruction_template.strip()

  Phase 2 Success Criteria

  - GroupChatManager enables multi-agent collaboration
  - Workflow templates provide structured agent interactions
  - Handoff system passes context between agents effectively
  - Complex analytical workflows execute successfully
  - Agent-to-agent communication follows proper ADK patterns

  ---
  Phase 3: Advanced Tool Integration 🔧

  Objective: Extend ADK capabilities with comprehensive tool ecosystem

  3.1 OpenAPI Tool Integration

  File: backend/app/tools/adk_openapi_tools.py

  from typing import Dict, Any, List, Optional
  from google.adk.tools import OpenAPITool
  from app.services.hitl_safety_service import HITLSafetyService
  import structlog

  logger = structlog.get_logger(__name__)

  class BMADOpenAPITool:
      """BMAD wrapper for ADK OpenAPI tools with enterprise controls."""

      def __init__(self, openapi_spec: Dict[str, Any], tool_name: str):
          self.tool_name = tool_name
          self.openapi_spec = openapi_spec
          self.hitl_service = HITLSafetyService()
          self.adk_tool = None

      async def initialize(self) -> bool:
          """Initialize the ADK OpenAPI tool."""
          try:
              self.adk_tool = OpenAPITool(
                  name=self.tool_name,
                  openapi_spec=self.openapi_spec,
                  description=f"OpenAPI integration for {self.tool_name}"
              )

              logger.info("OpenAPI tool initialized", tool_name=self.tool_name)
              return True

          except Exception as e:
              logger.error("OpenAPI tool initialization failed",
                          tool_name=self.tool_name, error=str(e))
              return False

      async def execute_with_approval(self,
                                     endpoint: str,
                                     method: str,
                                     parameters: Dict[str, Any],
                                     project_id: str,
                                     task_id: str) -> Dict[str, Any]:
          """Execute API call with HITL approval."""

          # Risk assessment
          risk_level = self._assess_api_risk(endpoint, method, parameters)

          if risk_level == "high":
              # Request HITL approval
              approval_id = await self.hitl_service.create_approval_request(
                  project_id=project_id,
                  task_id=task_id,
                  agent_type="api_integration",
                  request_type="API_CALL",
                  request_data={
                      "tool_name": self.tool_name,
                      "endpoint": endpoint,
                      "method": method,
                      "parameters": parameters,
                      "risk_level": risk_level
                  }
              )

              approval = await self.hitl_service.wait_for_approval(
                  approval_id, timeout_minutes=10
              )

              if not approval.approved:
                  return {
                      "success": False,
                      "error": "API call denied by human oversight"
                  }

          try:
              # Execute the API call through ADK
              result = await self.adk_tool.execute(
                  endpoint=endpoint,
                  method=method,
                  **parameters
              )

              return {
                  "success": True,
                  "result": result,
                  "tool_name": self.tool_name
              }

          except Exception as e:
              logger.error("OpenAPI tool execution failed",
                          tool_name=self.tool_name, error=str(e))
              return {
                  "success": False,
                  "error": str(e)
              }

      def _assess_api_risk(self, endpoint: str, method: str,
                          parameters: Dict[str, Any]) -> str:
          """Assess risk level of API operation."""
          # High risk for write operations
          if method.upper() in ["POST", "PUT", "DELETE", "PATCH"]:
              return "high"

          # High risk for admin endpoints
          admin_patterns = ["admin", "config", "settings", "delete"]
          if any(pattern in endpoint.lower() for pattern in admin_patterns):
              return "high"

          return "low"

  3.2 Tool Registry System

  File: backend/app/tools/adk_tool_registry.py

  from typing import Dict, Any, List, Optional, Type
  from google.adk.tools import BaseTool, FunctionTool
  from app.tools.adk_openapi_tools import BMADOpenAPITool
  import structlog

  logger = structlog.get_logger(__name__)

  class ADKToolRegistry:
      """Registry for managing ADK tools with BMAD integration."""

      def __init__(self):
          self.registered_tools: Dict[str, BaseTool] = {}
          self.openapi_tools: Dict[str, BMADOpenAPITool] = {}
          self.function_tools: Dict[str, FunctionTool] = {}

      def register_function_tool(self, name: str, func: callable,
                               description: str) -> bool:
          """Register a custom function as ADK tool."""
          try:
              tool = FunctionTool(
                  func=func,
                  description=description
              )

              self.function_tools[name] = tool
              self.registered_tools[name] = tool

              logger.info("Function tool registered", tool_name=name)
              return True

          except Exception as e:
              logger.error("Function tool registration failed",
                          tool_name=name, error=str(e))
              return False

      async def register_openapi_tool(self, name: str,
                                     openapi_spec: Dict[str, Any]) -> bool:
          """Register OpenAPI specification as ADK tool."""
          try:
              bmad_tool = BMADOpenAPITool(openapi_spec, name)

              if await bmad_tool.initialize():
                  self.openapi_tools[name] = bmad_tool
                  self.registered_tools[name] = bmad_tool.adk_tool

                  logger.info("OpenAPI tool registered", tool_name=name)
                  return True
              else:
                  return False

          except Exception as e:
              logger.error("OpenAPI tool registration failed",
                          tool_name=name, error=str(e))
              return False

      def get_tools_for_agent(self, agent_type: str) -> List[BaseTool]:
          """Get appropriate tools for specific agent type."""
          tool_mappings = {
              "analyst": ["data_analysis", "report_generator"],
              "architect": ["system_design", "api_validator"],
              "coder": ["code_generator", "syntax_checker", "api_client"],
              "tester": ["test_runner", "coverage_analyzer"],
              "deployer": ["deployment_tools", "health_checker"]
          }

          agent_tools = []
          tool_names = tool_mappings.get(agent_type, [])

          for tool_name in tool_names:
              if tool_name in self.registered_tools:
                  agent_tools.append(self.registered_tools[tool_name])

          return agent_tools

      def list_available_tools(self) -> Dict[str, List[str]]:
          """List all available tools by category."""
          return {
              "function_tools": list(self.function_tools.keys()),
              "openapi_tools": list(self.openapi_tools.keys()),
              "total_tools": len(self.registered_tools)
          }

  3.3 Specialized Tool Implementations

  File: backend/app/tools/specialized_adk_tools.py

  from typing import Dict, Any, List
  import json
  import httpx
  from app.tools.adk_tool_registry import ADKToolRegistry

  # Initialize registry
  tool_registry = ADKToolRegistry()

  # Code Analysis Tool
  def analyze_code_quality(code: str, language: str = "python") -> Dict[str, Any]:
      """Analyze code quality and provide recommendations."""

      # Simple code quality analysis (can be enhanced)
      lines = code.split('\n')

      analysis = {
          "total_lines": len(lines),
          "blank_lines": sum(1 for line in lines if line.strip() == ""),
          "comment_lines": sum(1 for line in lines if line.strip().startswith('#')),
          "complexity_score": min(len(lines) / 10, 10),  # Simple metric
          "recommendations": []
      }

      # Add recommendations
      if analysis["total_lines"] > 100:
          analysis["recommendations"].append("Consider breaking into smaller functions")

      if analysis["comment_lines"] / analysis["total_lines"] < 0.1:
          analysis["recommendations"].append("Add more comments for maintainability")

      return analysis

  # API Health Check Tool
  async def check_api_health(api_url: str, timeout: int = 5) -> Dict[str, Any]:
      """Check API endpoint health and response time."""

      try:
          async with httpx.AsyncClient() as client:
              response = await client.get(f"{api_url}/health", timeout=timeout)

              return {
                  "status": "healthy" if response.status_code == 200 else "unhealthy",
                  "status_code": response.status_code,
                  "response_time": response.elapsed.total_seconds(),
                  "endpoint": api_url
              }

      except Exception as e:
          return {
              "status": "error",
              "error": str(e),
              "endpoint": api_url
          }

  # Database Query Tool (Safe read-only)
  def query_project_metrics(project_id: str) -> Dict[str, Any]:
      """Query project metrics from database (read-only)."""

      # Mock implementation - replace with actual database query
      return {
          "project_id": project_id,
          "total_tasks": 15,
          "completed_tasks": 12,
          "success_rate": 0.8,
          "avg_completion_time": "2.5 hours",
          "agent_utilization": {
              "analyst": 0.7,
              "architect": 0.6,
              "coder": 0.9
          }
      }

  # Register tools
  def register_specialized_tools():
      """Register all specialized tools."""

      tool_registry.register_function_tool(
          "code_analyzer",
          analyze_code_quality,
          "Analyze code quality and provide improvement recommendations"
      )

      tool_registry.register_function_tool(
          "api_health_checker",
          check_api_health,
          "Check API endpoint health and response times"
      )

      tool_registry.register_function_tool(
          "project_metrics_query",
          query_project_metrics,
          "Query project metrics and performance data"
      )

      return tool_registry

  # Initialize on import
  specialized_registry = register_specialized_tools()

  Phase 3 Success Criteria

  - OpenAPI tools integrate external services safely
  - Tool registry manages comprehensive tool ecosystem
  - Specialized tools provide enhanced agent capabilities
  - HITL approval system governs high-risk tool operations
  - Agent-specific tool assignments optimize performance

  ---
  🎯 Implementation Timeline & Milestones

  Week 1-2: Agent Factory Integration

  - Update agent factory for ADK support
  - Implement feature flag system
  - Create configuration management
  - Deploy gradual rollout for analysts
  - Monitor performance and error rates

  Week 3-5: Multi-Agent Orchestration

  - Implement GroupChatManager integration
  - Create workflow templates
  - Build agent handoff system
  - Test complex multi-agent scenarios
  - Performance optimization

  Week 6-8: Advanced Tool Integration

  - Implement OpenAPI tool wrapper
  - Build comprehensive tool registry
  - Create specialized tools
  - Integrate HITL approval for tools
  - Final testing and deployment

  🚨 Risk Mitigation

  Technical Risks

  1. ADK API Changes - Pin ADK versions, comprehensive testing
  2. Performance Impact - Monitor response times, implement caching
  3. Integration Complexity - Modular implementation, rollback plans

  Business Risks

  1. Feature Regression - Comprehensive testing before each phase
  2. User Experience - Gradual rollout with feedback collection
  3. Cost Management - Usage monitoring and budget controls

  ✅ Success Metrics

  Phase 1: Agent Factory Integration

  - 95%+ successful ADK agent creation
  - <500ms factory response time
  - Zero legacy agent disruption

  Phase 2: Multi-Agent Orchestration

  - 3+ agent collaborative workflows working
  - <30s workflow initialization time
  - Successful agent handoffs in 90%+ cases

  Phase 3: Advanced Tool Integration

  - 5+ specialized tools operational
  - 100% HITL approval for high-risk operations
  - <2s tool execution time average

  ---
  This comprehensive plan provides clear implementation steps, success criteria, and risk mitigation for completing the
  outstanding ADK features. Each phase builds incrementally, ensuring stability and maintainability throughout the
  implementation process.