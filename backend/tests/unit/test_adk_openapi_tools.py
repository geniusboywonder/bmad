"""Tests for ADK OpenAPI Tools."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json

from app.tools.adk_openapi_tools import BMADOpenAPITool


@pytest.fixture
def sample_openapi_spec():
    """Sample OpenAPI specification for testing."""
    return {
        "openapi": "3.0.1",
        "info": {
            "title": "Test API",
            "version": "1.0.0"
        },
        "servers": [
            {
                "url": "https://api.test.com/v1"
            }
        ],
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {
                        "200": {
                            "description": "Success"
                        }
                    }
                },
                "post": {
                    "summary": "Create user",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Created"
                        }
                    }
                }
            },
            "/users/{id}": {
                "get": {
                    "summary": "Get user by ID",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success"
                        }
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer"
                }
            }
        }
    }


@pytest.fixture
def openapi_tool(sample_openapi_spec):
    """Create a BMAD OpenAPI tool instance for testing."""
    return BMADOpenAPITool(sample_openapi_spec, "test_api_tool")


class TestBMADOpenAPITool:
    """Test BMAD OpenAPI Tool functionality."""

    def test_tool_initialization(self, openapi_tool, sample_openapi_spec):
        """Test tool initialization with OpenAPI spec."""
        assert openapi_tool.tool_name == "test_api_tool"
        assert openapi_tool.openapi_spec == sample_openapi_spec
        assert openapi_tool.base_url == "https://api.test.com/v1"
        assert len(openapi_tool.endpoints) == 2  # /users and /users/{id}
        assert "bearerAuth" in openapi_tool.security_schemes

    def test_tool_initialization_invalid_spec(self):
        """Test tool initialization with invalid OpenAPI spec."""
        invalid_spec = {
            "info": {"title": "Test"}
            # Missing required fields
        }

        tool = BMADOpenAPITool(invalid_spec, "invalid_tool")
        result = tool.initialize()
        assert result is False

    def test_validate_openapi_spec_valid(self, openapi_tool):
        """Test validation of valid OpenAPI spec."""
        result = openapi_tool._validate_openapi_spec()
        assert result is True

    def test_validate_openapi_spec_missing_openapi(self):
        """Test validation with missing openapi field."""
        invalid_spec = {
            "info": {"title": "Test"},
            "paths": {}
        }

        tool = BMADOpenAPITool(invalid_spec, "invalid_tool")
        result = tool._validate_openapi_spec()
        assert result is False

    def test_validate_openapi_spec_missing_info(self):
        """Test validation with missing info field."""
        invalid_spec = {
            "openapi": "3.0.1",
            "paths": {}
        }

        tool = BMADOpenAPITool(invalid_spec, "invalid_tool")
        result = tool._validate_openapi_spec()
        assert result is False

    def test_validate_openapi_spec_missing_paths(self):
        """Test validation with missing paths field."""
        invalid_spec = {
            "openapi": "3.0.1",
            "info": {"title": "Test"}
        }

        tool = BMADOpenAPITool(invalid_spec, "invalid_tool")
        result = tool._validate_openapi_spec()
        assert result is False

    def test_extract_base_url_with_servers(self, sample_openapi_spec):
        """Test base URL extraction when servers are defined."""
        tool = BMADOpenAPITool(sample_openapi_spec, "test_tool")
        assert tool.base_url == "https://api.test.com/v1"

    def test_extract_base_url_without_servers(self):
        """Test base URL extraction when servers are not defined."""
        spec_without_servers = {
            "openapi": "3.0.1",
            "info": {"title": "Test API"},
            "paths": {}
        }

        tool = BMADOpenAPITool(spec_without_servers, "test_tool")
        assert tool.base_url == "https://test-api.example.com"

    def test_extract_endpoints(self, sample_openapi_spec):
        """Test endpoint extraction from OpenAPI spec."""
        tool = BMADOpenAPITool(sample_openapi_spec, "test_tool")
        endpoints = tool.endpoints

        assert "GET /users" in endpoints
        assert "POST /users" in endpoints
        assert "GET /users/{id}" in endpoints

        assert endpoints["GET /users"]["summary"] == "Get users"
        assert endpoints["POST /users"]["summary"] == "Create user"

    def test_extract_security_schemes(self, sample_openapi_spec):
        """Test security schemes extraction."""
        tool = BMADOpenAPITool(sample_openapi_spec, "test_tool")
        assert "bearerAuth" in tool.security_schemes
        assert tool.security_schemes["bearerAuth"]["type"] == "http"

    def test_build_headers_default(self, openapi_tool):
        """Test building default headers."""
        parameters = {}
        headers = openapi_tool._build_headers(parameters)

        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == "BMAD-ADK-Tool/test_api_tool"

    def test_build_headers_with_custom(self, openapi_tool):
        """Test building headers with custom headers."""
        parameters = {
            "headers": {
                "Authorization": "Bearer token123",
                "X-Custom": "value"
            }
        }
        headers = openapi_tool._build_headers(parameters)

        assert headers["Authorization"] == "Bearer token123"
        assert headers["X-Custom"] == "value"
        assert headers["Content-Type"] == "application/json"  # Still includes default

    def test_generate_tool_description(self, openapi_tool):
        """Test tool description generation."""
        description = openapi_tool._generate_tool_description()

        assert "OpenAPI tool for test_api_tool" in description
        assert "Base URL: https://api.test.com/v1" in description
        assert "Available endpoints:" in description
        assert "GET /users: Get users" in description
        assert "POST /users: Create user" in description
        assert "enterprise safety controls" in description

    def test_get_tool_info(self, openapi_tool):
        """Test getting tool information."""
        info = openapi_tool.get_tool_info()

        assert info["tool_name"] == "test_api_tool"
        assert info["is_initialized"] is False  # Not initialized yet
        assert info["base_url"] == "https://api.test.com/v1"
        assert info["endpoint_count"] == 2
        assert "bearerAuth" in info["security_schemes"]
        assert info["adk_tool_available"] is None  # Not initialized

    def test_assess_api_risk_low(self, openapi_tool):
        """Test risk assessment for low-risk operations."""
        # GET request
        risk = openapi_tool._assess_api_risk("/users", "GET", {})
        assert risk == "low"

        # HEAD request
        risk = openapi_tool._assess_api_risk("/health", "HEAD", {})
        assert risk == "low"

    def test_assess_api_risk_medium(self, openapi_tool):
        """Test risk assessment for medium-risk operations."""
        # PATCH request
        risk = openapi_tool._assess_api_risk("/users/123", "PATCH", {})
        assert risk == "medium"

    def test_assess_api_risk_high_write_operations(self, openapi_tool):
        """Test risk assessment for high-risk write operations."""
        # POST request
        risk = openapi_tool._assess_api_risk("/users", "POST", {})
        assert risk == "high"

        # PUT request
        risk = openapi_tool._assess_api_risk("/users/123", "PUT", {})
        assert risk == "high"

        # DELETE request
        risk = openapi_tool._assess_api_risk("/users/123", "DELETE", {})
        assert risk == "high"

    def test_assess_api_risk_high_admin_endpoints(self, openapi_tool):
        """Test risk assessment for high-risk admin endpoints."""
        risk = openapi_tool._assess_api_risk("/admin/users", "GET", {})
        assert risk == "high"

        risk = openapi_tool._assess_api_risk("/config/settings", "GET", {})
        assert risk == "high"

        risk = openapi_tool._assess_api_risk("/system/delete", "POST", {})
        assert risk == "high"

    def test_assess_api_risk_high_sensitive_data(self, openapi_tool):
        """Test risk assessment for high-risk sensitive data operations."""
        parameters = {
            "password": "secret123",
            "token": "abc123"
        }
        risk = openapi_tool._assess_api_risk("/users", "POST", parameters)
        assert risk == "high"

    def test_sanitize_parameters_for_approval(self, openapi_tool):
        """Test parameter sanitization for HITL approval."""
        parameters = {
            "username": "john_doe",
            "password": "secret123",
            "token": "abc123",
            "email": "john@example.com",
            "long_description": "A" * 150  # Long string
        }

        sanitized = openapi_tool._sanitize_parameters_for_approval(parameters)

        assert sanitized["username"] == "john_doe"
        assert sanitized["password"] == "***MASKED***"
        assert sanitized["token"] == "***MASKED***"
        assert sanitized["email"] == "john@example.com"
        assert sanitized["long_description"].endswith("...")  # Truncated
        assert len(sanitized["long_description"]) < 150

    def test_estimate_tokens(self, openapi_tool):
        """Test token estimation for usage tracking."""
        parameters = {"key": "value", "number": 123}
        result = {"success": True, "data": {"id": 1, "name": "test"}}

        tokens = openapi_tool._estimate_request_tokens(parameters, result)
        assert tokens > 0
        assert isinstance(tokens, int)

    def test_estimate_response_tokens(self, openapi_tool):
        """Test response token estimation."""
        result = {"success": True, "data": {"items": [1, 2, 3]}}
        tokens = openapi_tool._estimate_response_tokens(result)
        assert tokens > 0
        assert isinstance(tokens, int)


class TestBMADOpenAPIToolExecution:
    """Test OpenAPI tool execution with enterprise controls."""

    @pytest.fixture
    def initialized_tool(self, sample_openapi_spec):
        """Create an initialized OpenAPI tool."""
        tool = BMADOpenAPITool(sample_openapi_spec, "test_api_tool")
        # Mock successful initialization
        with patch.object(tool, '_validate_openapi_spec', return_value=True):
            with patch('google.adk.tools.FunctionTool') as mock_adk_tool:
                mock_adk_tool.return_value = Mock()
                result = tool.initialize()
                assert result is True
        return tool

    @patch('httpx.AsyncClient')
    def test_execute_api_call_success(self, mock_client_class, initialized_tool):
        """Test successful API call execution."""
        # Mock HTTP client
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "name": "test"}
        mock_response.headers = {"content-type": "application/json"}
        mock_response.url = "https://api.test.com/v1/users"
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        result = initialized_tool._execute_api_call("/users", "GET")

        assert result["success"] is True
        assert result["status_code"] == 200
        assert result["data"] == {"id": 1, "name": "test"}
        assert result["url"] == "https://api.test.com/v1/users"

    @patch('httpx.AsyncClient')
    def test_execute_api_call_with_body(self, mock_client_class, initialized_tool):
        """Test API call execution with request body."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 2, "created": True}
        mock_response.headers = {"content-type": "application/json"}
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        parameters = {"body": {"name": "new_user", "email": "user@test.com"}}
        result = initialized_tool._execute_api_call("/users", "POST", parameters)

        assert result["success"] is True
        assert result["status_code"] == 201

        # Verify request was made with correct body
        call_args = mock_client.request.call_args
        assert call_args[1]["json"] == {"name": "new_user", "email": "user@test.com"}

    @patch('httpx.AsyncClient')
    def test_execute_api_call_timeout(self, mock_client_class, initialized_tool):
        """Test API call execution with timeout."""
        from httpx import TimeoutException

        mock_client = AsyncMock()
        mock_client.request.side_effect = TimeoutException("Request timed out")
        mock_client_class.return_value.__aenter__.return_value = mock_client

        result = initialized_tool._execute_api_call("/users", "GET")

        assert result["success"] is False
        assert result["error"] == "Request timeout"
        assert result["status_code"] == 408

    @patch('httpx.AsyncClient')
    def test_execute_api_call_connection_error(self, mock_client_class, initialized_tool):
        """Test API call execution with connection error."""
        from httpx import ConnectError

        mock_client = AsyncMock()
        mock_client.request.side_effect = ConnectError("Connection failed")
        mock_client_class.return_value.__aenter__.return_value = mock_client

        result = initialized_tool._execute_api_call("/users", "GET")

        assert result["success"] is False
        assert result["error"] == "Connection failed"
        assert result["status_code"] == 503

    def test_execute_with_enterprise_controls_not_initialized(self, openapi_tool):
        """Test execution with enterprise controls when tool is not initialized."""
        result = openapi_tool.execute_with_enterprise_controls(
            "/users", "GET", {}, "test_project", "test_task", "analyst"
        )

        assert result["success"] is False
        assert result["error"] == "Tool not initialized"

    def test_execute_with_enterprise_controls_low_risk(self, initialized_tool):
        """Test execution with enterprise controls for low-risk operation."""
        with patch.object(initialized_tool, '_execute_api_call') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "status_code": 200,
                "data": {"users": []}
            }

            with patch.object(initialized_tool, '_track_api_usage'):
                result = initialized_tool.execute_with_enterprise_controls(
                    "/users", "GET", {}, "test_project", "test_task", "analyst"
                )

                assert result["success"] is True
                assert result["risk_level"] == "low"
                assert "execution_id" in result
                mock_execute.assert_called_once()

    def test_execute_with_enterprise_controls_high_risk_approved(self, initialized_tool):
        """Test execution with enterprise controls for high-risk operation with approval."""
        with patch.object(initialized_tool, '_execute_api_call') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "status_code": 201,
                "data": {"id": 1}
            }

            with patch.object(initialized_tool, '_track_api_usage'):
                with patch.object(initialized_tool.hitl_service, 'create_approval_request') as mock_approval:
                    mock_approval.return_value = "approval_123"

                    with patch.object(initialized_tool.hitl_service, 'wait_for_approval') as mock_wait:
                        mock_approval_result = Mock()
                        mock_approval_result.approved = True
                        mock_wait.return_value = mock_approval_result

                        result = initialized_tool.execute_with_enterprise_controls(
                            "/users", "POST", {"body": {"name": "test"}},
                            "test_project", "test_task", "analyst"
                        )

                        assert result["success"] is True
                        assert result["risk_level"] == "high"
                        mock_approval.assert_called_once()
                        mock_wait.assert_called_once()

    def test_execute_with_enterprise_controls_high_risk_denied(self, initialized_tool):
        """Test execution with enterprise controls for high-risk operation denied."""
        with patch.object(initialized_tool.hitl_service, 'create_approval_request') as mock_approval:
            mock_approval.return_value = "approval_123"

            with patch.object(initialized_tool.hitl_service, 'wait_for_approval') as mock_wait:
                mock_approval_result = Mock()
                mock_approval_result.approved = False
                mock_wait.return_value = mock_approval_result

                result = initialized_tool.execute_with_enterprise_controls(
                    "/users", "DELETE", {}, "test_project", "test_task", "analyst"
                )

                assert result["success"] is False
                assert "denied by human oversight" in result["error"]
                assert result["risk_level"] == "high"

    def test_execute_with_enterprise_controls_execution_error(self, initialized_tool):
        """Test execution with enterprise controls when API call fails."""
        with patch.object(initialized_tool, '_execute_api_call') as mock_execute:
            mock_execute.return_value = {
                "success": False,
                "error": "API Error",
                "status_code": 500
            }

            with patch.object(initialized_tool, '_track_api_usage'):
                result = initialized_tool.execute_with_enterprise_controls(
                    "/users", "GET", {}, "test_project", "test_task", "analyst"
                )

                assert result["success"] is False
                assert result["error"] == "API execution failed: API Error"
