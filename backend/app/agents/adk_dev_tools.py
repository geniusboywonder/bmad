"""ADK Development Tooling Integration for BMAD.

This module provides comprehensive development tooling that combines:
- ADK's built-in development UI for agent testing
- BMAD's enterprise testing and validation frameworks
- Performance benchmarking and evaluation systems
- Development-time HITL simulation
- Integrated testing harness for agent validation
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import structlog

# BMAD enterprise services
from app.services.hitl_safety_service import HITLSafetyService
from app.services.llm_monitoring import LLMUsageTracker
from app.config import settings

logger = structlog.get_logger(__name__)


@dataclass
class AgentBenchmarkResult:
    """Results from agent performance benchmarking."""
    agent_type: str
    task_type: str
    execution_time: float
    token_usage: int
    success_rate: float
    quality_score: float
    hitl_interventions: int
    error_count: int
    timestamp: datetime


@dataclass
class TestScenario:
    """Test scenario for agent validation."""
    scenario_id: str
    name: str
    description: str
    task_type: str
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    risk_level: str
    tags: List[str]


class ADKDevUI:
    """ADK Development UI integration for BMAD agents."""

    def __init__(self):
        self.hitl_service = HITLSafetyService()
        self.usage_tracker = LLMUsageTracker(enable_tracking=settings.llm_enable_usage_tracking)
        self.test_scenarios: Dict[str, TestScenario] = {}
        self.benchmark_results: List[AgentBenchmarkResult] = []
        self.hitl_simulation_mode = False  # Initialize HITL simulation mode

    async def launch_dev_interface(self, agent_type: str = "all") -> Dict[str, Any]:
        """Launch ADK development interface for agent testing.

        Args:
            agent_type: Type of agent to test ('all' for comprehensive testing)

        Returns:
            Development interface configuration and status
        """
        logger.info("Launching ADK development interface", agent_type=agent_type)

        interface_config = {
            "interface_type": "adk_development_ui",
            "agent_type": agent_type,
            "features": [
                "real_time_testing",
                "performance_monitoring",
                "hitl_simulation",
                "benchmarking_tools",
                "error_analysis",
                "trace_debugging"
            ],
            "endpoints": {
                "test_execution": "/dev/adk/test",
                "benchmark_run": "/dev/adk/benchmark",
                "hitl_simulate": "/dev/adk/hitl-simulate",
                "performance_dashboard": "/dev/adk/dashboard"
            },
            "status": "active"
        }

        # Initialize development environment
        await self._initialize_dev_environment(agent_type)

        logger.info("ADK development interface launched successfully")
        return interface_config

    async def _initialize_dev_environment(self, agent_type: str):
        """Initialize development environment components."""
        # Set up test scenarios
        await self._load_test_scenarios(agent_type)

        # Initialize benchmarking tools
        await self._setup_benchmarking_tools()

        # Configure HITL simulation
        await self._configure_hitl_simulation()

        logger.info("Development environment initialized", agent_type=agent_type)

    async def _load_test_scenarios(self, agent_type: str):
        """Load predefined test scenarios for agent validation."""
        # Analyst test scenarios
        if agent_type in ["analyst", "all"]:
            self.test_scenarios.update({
                "analyst_basic_req": TestScenario(
                    scenario_id="analyst_basic_req",
                    name="Basic Requirements Analysis",
                    description="Test basic requirements gathering and analysis",
                    task_type="requirements_analysis",
                    input_data={
                        "project_description": "Build a simple task management web application",
                        "target_users": "Project managers and team members",
                        "constraints": ["Web-based", "Real-time updates", "Mobile responsive"]
                    },
                    expected_output={
                        "user_personas": ["Project Manager", "Team Member"],
                        "functional_requirements": ["Create tasks", "Assign tasks", "Track progress"],
                        "success_criteria": ["All core features working", "Good user experience"]
                    },
                    risk_level="low",
                    tags=["requirements", "analysis", "basic"]
                ),
                "analyst_complex_req": TestScenario(
                    scenario_id="analyst_complex_req",
                    name="Complex Requirements Analysis",
                    description="Test complex multi-stakeholder requirements analysis",
                    task_type="requirements_analysis",
                    input_data={
                        "project_description": "Enterprise-scale project management platform with advanced analytics",
                        "target_users": "Enterprise project managers, executives, team members",
                        "constraints": ["Enterprise security", "Scalability to 10k users", "Integration with existing tools"],
                        "compliance": ["GDPR", "SOX", "Industry-specific regulations"]
                    },
                    expected_output={
                        "user_personas": ["Enterprise PM", "Executive", "Team Member", "IT Admin"],
                        "functional_requirements": ["Advanced reporting", "Resource management", "Risk tracking"],
                        "non_functional_requirements": ["99.9% uptime", "Sub-second response times"],
                        "compliance_requirements": ["Data encryption", "Audit trails", "Access controls"]
                    },
                    risk_level="high",
                    tags=["requirements", "analysis", "enterprise", "compliance"]
                )
            })

        # Add scenarios for other agent types as needed
        logger.info("Test scenarios loaded", scenario_count=len(self.test_scenarios))

    async def _setup_benchmarking_tools(self):
        """Set up performance benchmarking tools."""
        # Initialize benchmarking metrics
        self.benchmark_metrics = {
            "execution_time": [],
            "token_usage": [],
            "success_rate": [],
            "quality_score": [],
            "error_rate": []
        }

        logger.info("Benchmarking tools configured")

    async def _configure_hitl_simulation(self):
        """Configure HITL simulation for development testing."""
        # Set up simulated HITL responses for testing
        self.hitl_simulation_mode = True
        self.simulated_responses = {
            "auto_approve": True,  # For development testing
            "approval_delay": 2,  # Simulated delay in seconds
            "rejection_scenarios": ["high_risk", "policy_violation"]
        }

        logger.info("HITL simulation configured")

    async def run_test_scenario(self, scenario_id: str, agent_instance) -> Dict[str, Any]:
        """Run a specific test scenario against an agent instance.

        Args:
            scenario_id: ID of the test scenario to run
            agent_instance: Agent instance to test

        Returns:
            Test execution results
        """
        if scenario_id not in self.test_scenarios:
            return {"error": f"Test scenario {scenario_id} not found"}

        scenario = self.test_scenarios[scenario_id]
        logger.info("Running test scenario", scenario_id=scenario_id, scenario_name=scenario.name)

        start_time = time.time()

        try:
            # Execute test scenario
            result = await self._execute_test_scenario(scenario, agent_instance)

            execution_time = time.time() - start_time

            # Record benchmark results
            benchmark_result = AgentBenchmarkResult(
                agent_type=agent_instance.agent_type.value,
                task_type=scenario.task_type,
                execution_time=execution_time,
                token_usage=result.get("token_usage", 0),
                success_rate=1.0 if result.get("success") else 0.0,
                quality_score=result.get("quality_score", 0.0),
                hitl_interventions=result.get("hitl_interventions", 0),
                error_count=1 if not result.get("success") else 0,
                timestamp=datetime.now()
            )

            self.benchmark_results.append(benchmark_result)

            # Generate test report
            test_report = {
                "scenario_id": scenario_id,
                "scenario_name": scenario.name,
                "execution_time": execution_time,
                "success": result.get("success", False),
                "quality_score": result.get("quality_score", 0.0),
                "benchmark_result": benchmark_result,
                "details": result
            }

            logger.info("Test scenario completed", scenario_id=scenario_id, success=result.get("success"))
            return test_report

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error("Test scenario failed", scenario_id=scenario_id, error=str(e))

            return {
                "scenario_id": scenario_id,
                "scenario_name": scenario.name,
                "execution_time": execution_time,
                "success": False,
                "error": str(e)
            }

    async def _execute_test_scenario(self, scenario: TestScenario, agent_instance) -> Dict[str, Any]:
        """Execute the actual test scenario logic."""
        # Create test task
        from app.models.task import Task
        from uuid import uuid4

        test_task = Task(
            task_id=uuid4(),
            project_id=uuid4(),
            instructions=f"Test scenario: {scenario.description}",
            status="pending",
            priority=1
        )

        # Create test context
        from app.models.context import ContextArtifact

        test_context = [
            ContextArtifact(
                context_id=uuid4(),
                source_agent="test_framework",
                artifact_type="test_input",
                content=scenario.input_data
            )
        ]

        # Execute agent task
        result = await agent_instance.execute_task(test_task, test_context)

        # Validate results against expected output
        validation_result = self._validate_test_results(result, scenario.expected_output)

        return {
            "success": result.get("success", False),
            "output": result,
            "validation": validation_result,
            "quality_score": validation_result.get("quality_score", 0.0),
            "token_usage": result.get("tokens_used", 0),
            "hitl_interventions": 0  # Would be tracked in real HITL scenarios
        }

    def _validate_test_results(self, actual_result: Dict[str, Any],
                             expected_output: Dict[str, Any]) -> Dict[str, Any]:
        """Validate test results against expected output."""
        validation_score = 0.0
        total_checks = 0
        passed_checks = 0

        # Basic validation logic - can be enhanced based on specific requirements
        for key, expected_value in expected_output.items():
            total_checks += 1
            if key in actual_result.get("output", {}):
                actual_value = actual_result["output"][key]
                # Simple validation - check if key exists and has content
                if actual_value and len(str(actual_value)) > 0:
                    passed_checks += 1
                    validation_score += 0.2  # Partial credit for having content
                else:
                    validation_score += 0.1  # Minimal credit for having the key
            else:
                validation_score += 0.0  # No credit if key missing

        quality_score = validation_score / max(total_checks, 1)

        return {
            "quality_score": quality_score,
            "passed_checks": passed_checks,
            "total_checks": total_checks,
            "validation_details": f"{passed_checks}/{total_checks} checks passed"
        }

    async def run_performance_benchmark(self, agent_instance, scenario_count: int = 5) -> Dict[str, Any]:
        """Run performance benchmarking against multiple scenarios.

        Args:
            agent_instance: Agent instance to benchmark
            scenario_count: Number of scenarios to run

        Returns:
            Benchmarking results and analysis
        """
        logger.info("Starting performance benchmark", scenario_count=scenario_count)

        benchmark_start = time.time()
        results = []

        # Run scenarios
        available_scenarios = [s for s in self.test_scenarios.keys()
                             if self.test_scenarios[s].task_type == "requirements_analysis"][:scenario_count]

        for scenario_id in available_scenarios:
            result = await self.run_test_scenario(scenario_id, agent_instance)
            results.append(result)

        benchmark_duration = time.time() - benchmark_start

        # Analyze results
        analysis = self._analyze_benchmark_results(results)

        benchmark_report = {
            "benchmark_duration": benchmark_duration,
            "scenarios_run": len(results),
            "results": results,
            "analysis": analysis,
            "recommendations": self._generate_benchmark_recommendations(analysis)
        }

        logger.info("Performance benchmark completed", duration=benchmark_duration, scenarios=len(results))
        return benchmark_report

    def _analyze_benchmark_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze benchmark results for performance insights."""
        if not results:
            return {"error": "No results to analyze"}

        successful_runs = [r for r in results if r.get("success")]
        execution_times = [r.get("execution_time", 0) for r in results]
        quality_scores = [r.get("quality_score", 0) for r in results]

        analysis = {
            "total_scenarios": len(results),
            "successful_runs": len(successful_runs),
            "success_rate": len(successful_runs) / len(results),
            "average_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
            "average_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "performance_metrics": {
                "min_execution_time": min(execution_times) if execution_times else 0,
                "max_execution_time": max(execution_times) if execution_times else 0,
                "execution_time_std": self._calculate_std(execution_times)
            }
        }

        return analysis

    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation of values."""
        if not values:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def _generate_benchmark_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on benchmark analysis."""
        recommendations = []

        success_rate = analysis.get("success_rate", 0)
        avg_time = analysis.get("average_execution_time", 0)
        avg_quality = analysis.get("average_quality_score", 0)

        if success_rate < 0.8:
            recommendations.append("Improve agent reliability - success rate below 80%")
        if avg_time > 30:
            recommendations.append("Optimize execution time - average exceeds 30 seconds")
        if avg_quality < 0.7:
            recommendations.append("Enhance output quality - average score below 70%")

        if not recommendations:
            recommendations.append("Agent performance is within acceptable ranges")

        return recommendations

    async def simulate_hitl_workflow(self, agent_instance, scenario_id: str) -> Dict[str, Any]:
        """Simulate HITL workflow for development testing.

        Args:
            agent_instance: Agent instance to test
            scenario_id: Test scenario to run

        Returns:
            HITL simulation results
        """
        logger.info("Starting HITL workflow simulation", scenario_id=scenario_id)

        # Run test scenario
        test_result = await self.run_test_scenario(scenario_id, agent_instance)

        # Simulate HITL interactions
        hitl_simulation = {
            "scenario_id": scenario_id,
            "test_result": test_result,
            "hitl_interactions": [],
            "approval_decisions": [],
            "intervention_points": []
        }

        # Simulate approval workflow
        if self.hitl_simulation_mode:
            # Simulate pre-execution approval
            hitl_simulation["hitl_interactions"].append({
                "type": "pre_execution_approval",
                "timestamp": datetime.now().isoformat(),
                "decision": "approved",
                "reason": "Development testing mode"
            })

            # Simulate response approval
            hitl_simulation["hitl_interactions"].append({
                "type": "response_approval",
                "timestamp": datetime.now().isoformat(),
                "decision": "approved",
                "reason": "Test scenario validation"
            })

        logger.info("HITL workflow simulation completed", scenario_id=scenario_id)
        return hitl_simulation

    def get_development_dashboard(self) -> Dict[str, Any]:
        """Get development dashboard with testing and benchmarking data."""
        dashboard = {
            "test_scenarios": {
                "total": len(self.test_scenarios),
                "by_type": {},
                "by_risk": {}
            },
            "benchmark_results": {
                "total_runs": len(self.benchmark_results),
                "recent_results": [r.__dict__ for r in self.benchmark_results[-5:]],
                "performance_summary": self._get_performance_summary()
            },
            "development_tools": {
                "hitl_simulation": self.hitl_simulation_mode,
                "benchmarking_enabled": True,
                "trace_debugging": True,
                "performance_monitoring": True
            },
            "recommendations": self._generate_development_recommendations()
        }

        # Categorize scenarios
        for scenario in self.test_scenarios.values():
            dashboard["test_scenarios"]["by_type"][scenario.task_type] = \
                dashboard["test_scenarios"]["by_type"].get(scenario.task_type, 0) + 1
            dashboard["test_scenarios"]["by_risk"][scenario.risk_level] = \
                dashboard["test_scenarios"]["by_risk"].get(scenario.risk_level, 0) + 1

        return dashboard

    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary from benchmark results."""
        if not self.benchmark_results:
            return {"message": "No benchmark results available"}

        recent_results = self.benchmark_results[-10:]  # Last 10 results

        return {
            "average_execution_time": sum(r.execution_time for r in recent_results) / len(recent_results),
            "average_success_rate": sum(r.success_rate for r in recent_results) / len(recent_results),
            "average_quality_score": sum(r.quality_score for r in recent_results) / len(recent_results),
            "total_errors": sum(r.error_count for r in recent_results)
        }

    def _generate_development_recommendations(self) -> List[str]:
        """Generate development recommendations based on current state."""
        recommendations = []

        if len(self.test_scenarios) < 5:
            recommendations.append("Add more test scenarios for comprehensive validation")

        if len(self.benchmark_results) < 3:
            recommendations.append("Run more benchmark tests to establish performance baselines")

        if not self.hitl_simulation_mode:
            recommendations.append("Enable HITL simulation for development testing")

        if not recommendations:
            recommendations.append("Development environment is well-configured")

        return recommendations


# Global development UI instance
dev_ui = ADKDevUI()


async def launch_adk_dev_ui(agent_type: str = "all") -> Dict[str, Any]:
    """Convenience function to launch ADK development UI."""
    return await dev_ui.launch_dev_interface(agent_type)


async def run_agent_test(scenario_id: str, agent_instance) -> Dict[str, Any]:
    """Convenience function to run agent test scenario."""
    return await dev_ui.run_test_scenario(scenario_id, agent_instance)


async def run_performance_benchmark(agent_instance, scenario_count: int = 5) -> Dict[str, Any]:
    """Convenience function to run performance benchmark."""
    return await dev_ui.run_performance_benchmark(agent_instance, scenario_count)


async def simulate_hitl_workflow(agent_instance, scenario_id: str) -> Dict[str, Any]:
    """Convenience function to simulate HITL workflow."""
    return await dev_ui.simulate_hitl_workflow(agent_instance, scenario_id)


def get_dev_dashboard() -> Dict[str, Any]:
    """Convenience function to get development dashboard."""
    return dev_ui.get_development_dashboard()
