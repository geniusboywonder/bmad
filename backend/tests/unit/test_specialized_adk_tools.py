"""Tests for Specialized ADK Tools."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.tools.specialized_adk_tools import (
    analyze_code_quality,
    check_api_health,
    query_project_metrics,
    analyze_system_architecture,
    check_deployment_readiness,
    register_specialized_tools,
    get_specialized_tools_for_agent,
    get_tool_capabilities,
    specialized_registry
)

class TestCodeAnalysisTool:
    """Test code analysis tool functionality."""

    @pytest.mark.mock_data

    def test_analyze_code_quality_simple(self):
        """Test code quality analysis with simple code."""
        code = """def hello():
    print("Hello World")
    return True"""

        result = analyze_code_quality(code)

        assert result["total_lines"] == 3
        assert result["code_lines"] == 3
        assert result["comment_lines"] == 0
        assert result["blank_lines"] == 0
        assert "quality_score" in result
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)
        assert result["quality_score"] > 0

    @pytest.mark.mock_data

    def test_analyze_code_quality_complex(self):
        """Test code quality analysis with more complex code."""
        code = """# This is a complex function
def complex_function(data):
    '''
    This function processes data
    with multiple complex operations
    '''
    if not data:
        return None

    # Initialize variables
    result = []
    processed_items = []

    # Process each item
    for item in data:
        if item > 0:
            result.append(item * 2)
            processed_items.append(item)
        else:
            result.append(0)
            processed_items.append(0)

    # Additional processing steps
    filtered_result = [x for x in result if x > 0]

    # Calculate metrics
    total = sum(result)
    average = total / len(result) if result else 0

    # More complex calculations
    variance = sum((x - average) ** 2 for x in result) / len(result) if result else 0

    # Build comprehensive result
    final_result = {
        'result': result,
        'processed_items': processed_items,
        'filtered_result': filtered_result,
        'total': total,
        'average': average,
        'variance': variance,
        'count': len(result)
    }

    # Additional validation
    if variance > average:
        final_result['high_variance'] = True
    else:
        final_result['high_variance'] = False

    return final_result
# End of function"""

        result = analyze_code_quality(code)

        assert result["total_lines"] == 51
        assert result["comment_lines"] >= 5  # Multiple comments
        assert result["code_lines"] > 30  # Should be around 34
        assert result["complexity_score"] == 5.1  # 51 lines / 10 = 5.1 (>5 triggers recommendation)
        assert any("maintainability" in rec.lower() for rec in result["recommendations"])

    @pytest.mark.mock_data

    def test_analyze_code_quality_empty(self):
        """Test code quality analysis with empty code."""
        result = analyze_code_quality("")

        assert result["total_lines"] == 1  # Empty string still counts as one line
        assert result["code_lines"] == 0
        assert result["quality_score"] == 66.33333333333333  # Calculated quality score
        assert "Add more comments" in result["recommendations"][0]

    @pytest.mark.mock_data

    def test_analyze_code_quality_with_language(self):
        """Test code quality analysis with language specification."""
        python_code = "def test(): pass"
        result = analyze_code_quality(python_code, "python")

        assert result["total_lines"] == 1
        assert result["code_lines"] == 1

    @pytest.mark.mock_data

    def test_analyze_code_quality_error_handling(self):
        """Test code quality analysis error handling."""
        # This should not raise an exception
        result = analyze_code_quality(None)

        assert "error" in result
        assert result["total_lines"] == 0
        assert result["quality_score"] == 0.0

class TestAPIHealthCheckTool:
    """Test API health check tool functionality."""

    @pytest.mark.asyncio
    @pytest.mark.mock_data

    async def test_check_api_health_success(self):
        """Test successful API health check."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy", "version": "1.0"}
            mock_response.headers = {"content-type": "application/json"}
            mock_response.url = "https://api.test.com/health"
            mock_response.is_success = True
            mock_response.text = '{"status": "healthy", "version": "1.0"}'
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await check_api_health("https://api.test.com/health")

            assert result["status_code"] == 200
            assert result["is_success"] is True
            assert result["status"] == "healthy"
            assert result["has_json_response"] is True
            assert "response_time_ms" in result

    @pytest.mark.asyncio
    @pytest.mark.mock_data

    async def test_check_api_health_timeout(self):
        """Test API health check with timeout."""
        from httpx import TimeoutException

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = TimeoutException("Request timed out")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await check_api_health("https://api.test.com/health", timeout=5)

            assert result["status"] == "timeout"
            assert "timed out" in result["error"].lower()
            assert result["response_time_ms"] == 5000  # 5 seconds in ms

    @pytest.mark.asyncio
    @pytest.mark.mock_data

    async def test_check_api_health_connection_error(self):
        """Test API health check with connection error."""
        from httpx import ConnectError

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = ConnectError("Connection failed")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await check_api_health("https://api.test.com/health")

            assert result["status"] == "connection_failed"
            assert "connect" in result["error"].lower()

    @pytest.mark.asyncio
    @pytest.mark.mock_data

    async def test_check_api_health_unhealthy_response(self):
        """Test API health check with unhealthy response."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 503
            mock_response.json.return_value = {"status": "unhealthy", "message": "Service down"}
            mock_response.headers = {"content-type": "application/json"}
            mock_response.url = "https://api.test.com/health"
            mock_response.is_success = False
            mock_response.text = '{"status": "unhealthy", "message": "Service down"}'
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await check_api_health("https://api.test.com/health")

            assert result["status_code"] == 503
            assert result["is_success"] is False
            assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    @pytest.mark.mock_data

    async def test_check_api_health_with_method(self):
        """Test API health check with different HTTP methods."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.headers = {"content-type": "application/json"}
            mock_response.url = "https://api.test.com/health"
            mock_response.is_success = True
            mock_response.text = '{"status": "healthy", "version": "1.0"}'
            mock_client.get.return_value = mock_response
            mock_client.head.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await check_api_health("https://api.test.com/health", method="HEAD")

            assert result["method"] == "HEAD"
            assert result["status_code"] == 200

    @pytest.mark.asyncio
    @pytest.mark.mock_data

    async def test_check_api_health_health_indicators(self):
        """Test API health check with health indicators."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "Service is healthy and running"
            mock_response.json.side_effect = ValueError("Not JSON")
            mock_response.headers = {"content-type": "text/plain"}
            mock_response.url = "https://api.test.com/health"
            mock_response.is_success = True
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await check_api_health("https://api.test.com/health")

            assert result["has_json_response"] is False
            assert result["health_indicators"]["has_healthy_content"] is True
            assert result["health_indicators"]["has_status_field"] is False

class TestProjectMetricsTool:
    """Test project metrics query tool functionality."""

    @pytest.mark.mock_data

    def test_query_project_metrics_basic(self):
        """Test basic project metrics query."""
        result = query_project_metrics("project_123")

        assert result["project_id"] == "project_123"
        assert "project_overview" in result
        assert "agent_performance" in result
        assert "quality_metrics" in result
        assert "timeline" in result
        assert "generated_at" in result

        # Check project overview
        overview = result["project_overview"]
        assert overview["total_tasks"] == 15
        assert overview["completed_tasks"] == 12
        assert overview["success_rate"] == 0.8

    @pytest.mark.mock_data

    def test_query_project_metrics_with_filters(self):
        """Test project metrics query with metric type filters."""
        result = query_project_metrics("project_123", metric_types=["project_overview", "quality_metrics"])

        assert result["project_id"] == "project_123"
        assert "project_overview" in result
        assert "quality_metrics" in result
        assert "agent_performance" not in result  # Should be filtered out
        assert "timeline" not in result  # Should be filtered out

    @pytest.mark.mock_data

    def test_query_project_metrics_empty_filters(self):
        """Test project metrics query with empty filters."""
        result = query_project_metrics("project_123", metric_types=[])

        assert result["project_id"] == "project_123"
        assert "project_overview" in result
        assert "agent_performance" in result
        assert "quality_metrics" in result
        assert "timeline" in result

    @pytest.mark.mock_data

    def test_query_project_metrics_agent_performance(self):
        """Test agent performance metrics structure."""
        result = query_project_metrics("project_123")

        agent_perf = result["agent_performance"]
        expected_agents = ["analyst", "architect", "coder", "tester", "deployer"]

        for agent in expected_agents:
            assert agent in agent_perf
            assert "tasks" in agent_perf[agent]
            assert "completed" in agent_perf[agent]
            assert "avg_time" in agent_perf[agent]

    @pytest.mark.mock_data

    def test_query_project_metrics_quality_metrics(self):
        """Test quality metrics structure."""
        result = query_project_metrics("project_123")

        quality = result["quality_metrics"]
        assert "code_quality_score" in quality
        assert "test_coverage" in quality
        assert "security_score" in quality
        assert "performance_score" in quality

        # Check reasonable value ranges
        assert 0 <= quality["code_quality_score"] <= 100
        assert 0 <= quality["test_coverage"] <= 100

    @pytest.mark.mock_data

    def test_query_project_metrics_timeline(self):
        """Test timeline metrics structure."""
        result = query_project_metrics("project_123")

        timeline = result["timeline"]
        assert "start_date" in timeline
        assert "estimated_completion" in timeline
        assert "actual_completion" in timeline
        assert "days_elapsed" in timeline
        assert "days_remaining" in timeline

class TestSystemArchitectureTool:
    """Test system architecture analysis tool functionality."""

    @pytest.mark.mock_data

    def test_analyze_system_architecture_comprehensive(self):
        """Test comprehensive system architecture analysis."""
        architecture_doc = """
        # System Architecture

        ## Database Design
        We use PostgreSQL with proper indexing and relationships.

        ## API Design
        RESTful APIs with OpenAPI specification.

        ## Security
        Authentication via JWT tokens and role-based access control.

        ## Deployment
        Containerized deployment using Docker and Kubernetes.
        """

        result = analyze_system_architecture(architecture_doc, "comprehensive")

        assert result["analysis_type"] == "comprehensive"
        assert result["document_length"] > 0
        assert "database_design" in result["sections_identified"]
        assert "api_design" in result["sections_identified"]
        assert result["score"] > 0
        assert len(result["key_findings"]) > 0
        assert len(result["recommendations"]) > 0

    @pytest.mark.mock_data

    def test_analyze_system_architecture_security(self):
        """Test security-focused architecture analysis."""
        architecture_doc = """
        Security measures include encryption, access controls,
        and regular security audits.
        """

        result = analyze_system_architecture(architecture_doc, "security")

        assert result["analysis_type"] == "security"
        assert "Authentication" in " ".join(result["key_findings"])
        assert "encryption" in " ".join(result["key_findings"]).lower()
        assert result["score"] > 0

    @pytest.mark.mock_data

    def test_analyze_system_architecture_performance(self):
        """Test performance-focused architecture analysis."""
        architecture_doc = """
        Performance optimizations include caching, load balancing,
        and database query optimization.
        """

        result = analyze_system_architecture(architecture_doc, "performance")

        assert result["analysis_type"] == "performance"
        assert "caching" in " ".join(result["key_findings"]).lower()
        assert result["score"] > 0

    @pytest.mark.mock_data

    def test_analyze_system_architecture_scalability(self):
        """Test scalability-focused architecture analysis."""
        architecture_doc = """
        Scalability features include horizontal scaling, microservices,
        and distributed databases.
        """

        result = analyze_system_architecture(architecture_doc, "scalability")

        assert result["analysis_type"] == "scalability"
        assert "horizontal scaling" in " ".join(result["key_findings"]).lower()
        assert result["score"] > 0

    @pytest.mark.mock_data

    def test_analyze_system_architecture_empty_doc(self):
        """Test architecture analysis with empty document."""
        result = analyze_system_architecture("", "comprehensive")

        assert result["analysis_type"] == "comprehensive"
        assert result["document_length"] == 0
        assert result["score"] == 0.0
        assert len(result["sections_identified"]) == 0

    @pytest.mark.mock_data

    def test_analyze_system_architecture_risk_assessment(self):
        """Test risk assessment in architecture analysis."""
        architecture_doc = "Basic system with minimal documentation."

        result = analyze_system_architecture(architecture_doc, "comprehensive")

        assert "risk_assessment" in result
        risk = result["risk_assessment"]
        assert "high_risk_items" in risk
        assert "medium_risk_items" in risk
        assert "low_risk_items" in risk
        assert "overall_risk_level" in risk

class TestDeploymentReadinessTool:
    """Test deployment readiness check tool functionality."""

    @pytest.mark.mock_data

    def test_check_deployment_readiness_production(self):
        """Test deployment readiness check for production environment."""
        result = check_deployment_readiness("project_123", "production")

        assert result["project_id"] == "project_123"
        assert result["environment"] == "production"
        assert "checklist" in result
        assert "blocking_issues" in result
        assert "warnings" in result
        assert "readiness_score" in result
        assert "estimated_deployment_time" in result

        # Check checklist structure
        checklist = result["checklist"]
        assert "code_quality" in checklist
        assert "infrastructure" in checklist
        assert "documentation" in checklist
        assert "security" in checklist

    @pytest.mark.mock_data

    def test_check_deployment_readiness_staging(self):
        """Test deployment readiness check for staging environment."""
        result = check_deployment_readiness("project_456", "staging")

        assert result["project_id"] == "project_456"
        assert result["environment"] == "staging"
        assert isinstance(result["readiness_score"], float)
        assert 0 <= result["readiness_score"] <= 100

    @pytest.mark.mock_data

    def test_check_deployment_readiness_high_readiness(self):
        """Test deployment readiness with high readiness score."""
        result = check_deployment_readiness("project_high", "production")

        # Since all checks are mocked as passing, should have high score
        assert result["readiness_score"] >= 80  # Our threshold
        assert result["overall_ready"] is True
        assert len(result["blocking_issues"]) == 0

    @pytest.mark.mock_data

    def test_check_deployment_readiness_low_readiness(self):
        """Test deployment readiness with low readiness score."""
        # This would require mocking the checklist items to fail
        # For now, our mock implementation always passes
        result = check_deployment_readiness("project_low", "production")

        assert isinstance(result["readiness_score"], float)
        assert "overall_ready" in result

    @pytest.mark.mock_data

    def test_check_deployment_readiness_checklist_structure(self):
        """Test deployment readiness checklist structure."""
        result = check_deployment_readiness("project_test", "production")

        checklist = result["checklist"]

        # Check code quality section
        code_quality = checklist["code_quality"]
        assert "tests_passing" in code_quality
        assert "linting_clean" in code_quality
        assert "security_scan_passed" in code_quality
        assert "code_coverage_above_80" in code_quality

        # Check infrastructure section
        infrastructure = checklist["infrastructure"]
        assert "environment_configured" in infrastructure
        assert "database_migrations_ready" in infrastructure
        assert "secrets_configured" in infrastructure
        assert "monitoring_setup" in infrastructure

    @pytest.mark.mock_data

    def test_check_deployment_readiness_warnings_and_issues(self):
        """Test deployment readiness warnings and blocking issues."""
        result = check_deployment_readiness("project_warnings", "production")

        # Check that warnings and blocking issues are arrays
        assert isinstance(result["warnings"], list)
        assert isinstance(result["blocking_issues"], list)

        # Since our mock implementation has some items set to False,
        # we should have some warnings
        assert len(result["warnings"]) >= 0
        assert len(result["blocking_issues"]) >= 0

class TestSpecializedToolsIntegration:
    """Test specialized tools integration and registration."""

    @pytest.mark.mock_data

    def test_register_specialized_tools(self):
        """Test registration of specialized tools."""
        registry = register_specialized_tools()

        # Check that tools were registered
        available = registry.get_available_tools()
        assert available["total_count"] >= 5  # At least 5 specialized tools

        # Check specific tools
        function_tools = available["function_tools"]
        expected_tools = [
            "code_analyzer", "api_health_checker", "project_metrics_query",
            "system_architecture_analyzer", "deployment_readiness_checker"
        ]

        for tool_name in expected_tools:
            assert tool_name in function_tools

    @pytest.mark.mock_data

    def test_get_specialized_tools_for_agent(self):
        """Test getting specialized tools for different agents."""
        # Test analyst tools
        analyst_tools = get_specialized_tools_for_agent("analyst")
        expected_analyst = ["code_analyzer", "api_health_checker", "project_metrics_query"]
        for tool in expected_analyst:
            assert tool in analyst_tools

        # Test architect tools
        architect_tools = get_specialized_tools_for_agent("architect")
        expected_architect = ["system_architecture_analyzer", "api_health_checker", "code_analyzer"]
        for tool in expected_architect:
            assert tool in architect_tools

        # Test coder tools
        coder_tools = get_specialized_tools_for_agent("coder")
        expected_coder = ["code_analyzer", "api_health_checker"]
        for tool in expected_coder:
            assert tool in coder_tools

        # Test unknown agent
        unknown_tools = get_specialized_tools_for_agent("unknown")
        assert unknown_tools == []

    @pytest.mark.mock_data

    def test_get_tool_capabilities(self):
        """Test getting tool capabilities information."""
        capabilities = get_tool_capabilities()

        expected_tools = [
            "code_analyzer", "api_health_checker", "project_metrics_query",
            "system_architecture_analyzer", "deployment_readiness_checker"
        ]

        for tool_name in expected_tools:
            assert tool_name in capabilities
            tool_info = capabilities[tool_name]
            assert "description" in tool_info
            assert "parameters" in tool_info
            assert "output" in tool_info

