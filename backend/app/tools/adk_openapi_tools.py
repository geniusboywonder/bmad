"""BMAD OpenAPI Tool Integration for ADK agents with enterprise controls."""

from typing import Dict, Any, List, Optional
import structlog
import httpx
import json
from datetime import datetime

from google.adk.tools import FunctionTool
from app.services.hitl_safety_service import HITLSafetyService
from app.services.llm_service import LLMService

logger = structlog.get_logger(__name__)


class BMADOpenAPITool:
    """BMAD wrapper for ADK OpenAPI tools with enterprise controls and HITL approval."""

    def __init__(self, openapi_spec: Dict[str, Any], tool_name: str):
        self.tool_name = tool_name
        self.openapi_spec = openapi_spec
        self.adk_tool = None
        self.hitl_service = HITLSafetyService()
        self.llm_service = LLMService({"enable_monitoring": True})
        self.is_initialized = False

        # Tool configuration
        self.base_url = self._extract_base_url()
        self.endpoints = self._extract_endpoints()
        self.security_schemes = self._extract_security_schemes()

        logger.info("BMAD OpenAPI tool created",
                   tool_name=tool_name,
                   base_url=self.base_url,
                   endpoint_count=len(self.endpoints))

    async def initialize(self) -> bool:
        """Initialize the ADK OpenAPI tool with validation."""
        try:
            # Validate OpenAPI spec
            if not self._validate_openapi_spec():
                logger.error("Invalid OpenAPI specification", tool_name=self.tool_name)
                return False

            # Create ADK FunctionTool wrapper
            self.adk_tool = FunctionTool(self._execute_api_call)

            self.is_initialized = True
            logger.info("BMAD OpenAPI tool initialized successfully", tool_name=self.tool_name)
            return True

        except Exception as e:
            logger.error("Failed to initialize BMAD OpenAPI tool",
                        tool_name=self.tool_name,
                        error=str(e))
            return False

    async def execute_with_enterprise_controls(self,
                                             endpoint: str,
                                             method: str,
                                             parameters: Dict[str, Any],
                                             project_id: str,
                                             task_id: str,
                                             agent_type: str) -> Dict[str, Any]:
        """Execute API call with full BMAD enterprise controls.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            parameters: Request parameters
            project_id: Project identifier
            task_id: Task identifier
            agent_type: Calling agent type

        Returns:
            API response with enterprise controls applied
        """
        if not self.is_initialized:
            return {
                "success": False,
                "error": "Tool not initialized"
            }

        execution_id = f"api_call_{self.tool_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # 1. Risk Assessment
            risk_level = self._assess_api_risk(endpoint, method, parameters)

            # 2. HITL Approval for High-Risk Operations
            if risk_level == "high":
                approval_result = await self._request_hitl_approval(
                    endpoint, method, parameters, project_id, task_id, agent_type, execution_id
                )
                if not approval_result["approved"]:
                    return {
                        "success": False,
                        "error": "API call denied by human oversight",
                        "execution_id": execution_id,
                        "risk_level": risk_level
                    }

            # 3. Execute API Call
            start_time = datetime.now()
            api_result = await self._execute_api_call(endpoint, method, parameters)
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # 4. Track Usage
            await self._track_api_usage(
                endpoint, method, parameters, api_result, execution_time,
                project_id, task_id, agent_type, risk_level
            )

            # 5. Return Enhanced Response
            result = {
                "success": api_result.get("success", False),
                "data": api_result.get("data"),
                "execution_id": execution_id,
                "execution_time": execution_time,
                "risk_level": risk_level,
                "tool_name": self.tool_name,
                "endpoint": endpoint,
                "method": method
            }

            # Propagate error if API call failed
            if not api_result.get("success", True) and "error" in api_result:
                result["error"] = f"API execution failed: {api_result['error']}"

            return result

        except Exception as e:
            error_msg = f"API execution failed: {str(e)}"
            logger.error("BMAD OpenAPI tool execution failed",
                        tool_name=self.tool_name,
                        endpoint=endpoint,
                        method=method,
                        execution_id=execution_id,
                        error=str(e))

            # Track failed usage
            await self._track_api_usage(
                endpoint, method, parameters, {"success": False, "error": str(e)}, 0,
                project_id, task_id, agent_type, "error"
            )

            return {
                "success": False,
                "error": error_msg,
                "execution_id": execution_id,
                "tool_name": self.tool_name
            }

    async def _execute_api_call(self, endpoint: str, method: str = "GET",
                               parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the actual API call with proper error handling.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            parameters: Request parameters

        Returns:
            API response data
        """
        try:
            parameters = parameters or {}

            # Build full URL
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

            # Prepare request data
            request_data = {
                "method": method.upper(),
                "url": url,
                "headers": self._build_headers(parameters),
                "timeout": 30.0
            }

            # Add request body for POST/PUT/PATCH
            if method.upper() in ["POST", "PUT", "PATCH"]:
                if "body" in parameters:
                    request_data["json"] = parameters["body"]
                elif "data" in parameters:
                    request_data["json"] = parameters["data"]

            # Add query parameters
            if "query" in parameters:
                request_data["params"] = parameters["query"]

            # Execute request
            async with httpx.AsyncClient() as client:
                response = await client.request(**request_data)

                # Parse response
                try:
                    response_data = response.json()
                except:
                    response_data = {"text": response.text}

                return {
                    "success": response.is_success,
                    "status_code": response.status_code,
                    "data": response_data,
                    "headers": dict(response.headers),
                    "url": str(response.url)
                }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Request timeout",
                "status_code": 408
            }
        except httpx.ConnectError:
            return {
                "success": False,
                "error": "Connection failed",
                "status_code": 503
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": 500
            }

    def _assess_api_risk(self, endpoint: str, method: str, parameters: Dict[str, Any]) -> str:
        """Assess risk level of API operation.

        Args:
            endpoint: API endpoint
            method: HTTP method
            parameters: Request parameters

        Returns:
            Risk level: "low", "medium", or "high"
        """
        # High risk for write operations
        if method.upper() in ["POST", "PUT", "DELETE", "PATCH"]:
            return "high"

        # High risk for admin endpoints
        admin_patterns = ["admin", "config", "settings", "delete", "drop", "truncate"]
        endpoint_lower = endpoint.lower()
        if any(pattern in endpoint_lower for pattern in admin_patterns):
            return "high"

        # High risk for sensitive data patterns
        sensitive_patterns = ["password", "secret", "token", "key", "credential"]
        param_keys = " ".join(parameters.keys()).lower() if parameters else ""
        if any(pattern in param_keys for pattern in sensitive_patterns):
            return "high"

        # Medium risk for data modification
        if method.upper() in ["PATCH"]:
            return "medium"

        return "low"

    async def _request_hitl_approval(self, endpoint: str, method: str, parameters: Dict[str, Any],
                                   project_id: str, task_id: str, agent_type: str,
                                   execution_id: str) -> Dict[str, Any]:
        """Request HITL approval for high-risk API operations.

        Args:
            endpoint: API endpoint
            method: HTTP method
            parameters: Request parameters
            project_id: Project identifier
            task_id: Task identifier
            agent_type: Calling agent type
            execution_id: Execution identifier

        Returns:
            Approval result
        """
        try:
            approval_id = await self.hitl_service.create_approval_request(
                project_id=project_id,
                task_id=task_id,
                agent_type=agent_type,
                request_type="API_CALL",
                request_data={
                    "tool_name": self.tool_name,
                    "endpoint": endpoint,
                    "method": method,
                    "parameters": self._sanitize_parameters_for_approval(parameters),
                    "risk_level": "high",
                    "execution_id": execution_id,
                    "base_url": self.base_url
                }
            )

            approval = await self.hitl_service.wait_for_approval(approval_id, timeout_minutes=10)
            return {
                "approved": approval.approved,
                "approval_id": approval_id
            }

        except Exception as e:
            logger.warning("HITL approval request failed for API call",
                         tool_name=self.tool_name,
                         endpoint=endpoint,
                         execution_id=execution_id,
                         error=str(e))
            return {"approved": False, "error": str(e)}

    def _sanitize_parameters_for_approval(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize parameters for HITL approval display.

        Args:
            parameters: Raw parameters

        Returns:
            Sanitized parameters safe for human review
        """
        sanitized = {}

        for key, value in parameters.items():
            if isinstance(value, dict):
                # Sanitize nested dictionaries
                sanitized[key] = self._sanitize_dict_for_approval(value)
            elif isinstance(value, str) and len(value) > 100:
                # Truncate long strings
                sanitized[key] = value[:100] + "..."
            elif key.lower() in ["password", "secret", "token", "key", "credential"]:
                # Mask sensitive data
                sanitized[key] = "***MASKED***"
            else:
                sanitized[key] = value

        return sanitized

    def _sanitize_dict_for_approval(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize dictionary for approval display."""
        sanitized = {}
        for key, value in data.items():
            if key.lower() in ["password", "secret", "token", "key", "credential"]:
                sanitized[key] = "***MASKED***"
            elif isinstance(value, str) and len(value) > 50:
                sanitized[key] = value[:50] + "..."
            else:
                sanitized[key] = value
        return sanitized

    async def _track_api_usage(self, endpoint: str, method: str, parameters: Dict[str, Any],
                             result: Dict[str, Any], execution_time: float,
                             project_id: str, task_id: str, agent_type: str, risk_level: str):
        """Track API usage for monitoring and analytics.

        Args:
            endpoint: API endpoint
            method: HTTP method
            parameters: Request parameters
            result: API response result
            execution_time: Execution time in seconds
            project_id: Project identifier
            task_id: Task identifier
            agent_type: Calling agent type
            risk_level: Assessed risk level
        """
        try:
            # Calculate estimated cost (simplified)
            estimated_tokens = self._estimate_request_tokens(parameters, result)
            estimated_cost = estimated_tokens * 0.00001  # Rough estimate

            self.llm_service.track_usage(
                agent_type=agent_type,
                tokens_used=estimated_tokens,
                response_time=execution_time,
                cost=estimated_cost,
                success=result.get("success", False),
                project_id=project_id,
                task_id=task_id,
                provider="external_api",
                model=self.tool_name,
                input_tokens=self._estimate_request_tokens(parameters, {}),
                output_tokens=self._estimate_response_tokens(result),
                api_endpoint=endpoint,
                http_method=method,
                risk_level=risk_level
            )

        except Exception as e:
            logger.warning("Failed to track API usage",
                         tool_name=self.tool_name,
                         endpoint=endpoint,
                         error=str(e))

    def _estimate_request_tokens(self, parameters: Dict[str, Any], result: Dict[str, Any]) -> int:
        """Estimate token usage for request.

        Args:
            parameters: Request parameters
            result: Response result

        Returns:
            Estimated token count
        """
        # Simple estimation based on content size
        param_str = json.dumps(parameters) if parameters else ""
        result_str = json.dumps(result) if result else ""

        total_chars = len(param_str) + len(result_str)
        # Rough estimate: 1 token per 4 characters
        return max(1, total_chars // 4)

    def _estimate_response_tokens(self, result: Dict[str, Any]) -> int:
        """Estimate token usage for response.

        Args:
            result: Response result

        Returns:
            Estimated token count
        """
        result_str = json.dumps(result) if result else ""
        return max(1, len(result_str) // 4)

    def _extract_base_url(self) -> str:
        """Extract base URL from OpenAPI spec.

        Returns:
            Base URL for API calls
        """
        servers = self.openapi_spec.get("servers", [])
        if servers:
            return servers[0].get("url", "https://api.example.com")

        # Fallback to info title-based URL
        title = self.openapi_spec.get("info", {}).get("title", "api").lower().replace(" ", "-")
        return f"https://{title}.example.com"

    def _extract_endpoints(self) -> Dict[str, Any]:
        """Extract endpoints from OpenAPI spec.

        Returns:
            Dictionary of endpoints by path and method
        """
        paths = self.openapi_spec.get("paths", {})
        endpoints = {}

        for path, methods in paths.items():
            for method, spec in methods.items():
                if method.lower() in ["get", "post", "put", "delete", "patch"]:
                    endpoints[f"{method.upper()} {path}"] = spec

        return endpoints

    def _extract_security_schemes(self) -> Dict[str, Any]:
        """Extract security schemes from OpenAPI spec.

        Returns:
            Dictionary of security schemes
        """
        return self.openapi_spec.get("components", {}).get("securitySchemes", {})

    def _validate_openapi_spec(self) -> bool:
        """Validate OpenAPI specification structure.

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if "openapi" not in self.openapi_spec:
                return False

            if "info" not in self.openapi_spec:
                return False

            if "paths" not in self.openapi_spec:
                return False

            # Validate OpenAPI version
            version = self.openapi_spec["openapi"]
            if not version.startswith("3."):
                logger.warning("OpenAPI version may not be fully supported",
                             version=version)

            return True

        except Exception as e:
            logger.error("OpenAPI spec validation failed", error=str(e))
            return False

    def _build_headers(self, parameters: Dict[str, Any]) -> Dict[str, str]:
        """Build request headers from parameters.

        Args:
            parameters: Request parameters

        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"BMAD-ADK-Tool/{self.tool_name}"
        }

        # Add custom headers from parameters
        if "headers" in parameters:
            headers.update(parameters["headers"])

        return headers

    def _generate_tool_description(self) -> str:
        """Generate tool description for ADK.

        Returns:
            Tool description string
        """
        description = f"OpenAPI tool for {self.tool_name}\n\n"
        description += f"Base URL: {self.base_url}\n\n"
        description += "Available endpoints:\n"

        for endpoint_name, spec in list(self.endpoints.items())[:5]:  # Limit to first 5
            operation_desc = spec.get("summary", spec.get("description", "No description"))
            description += f"- {endpoint_name}: {operation_desc}\n"

        if len(self.endpoints) > 5:
            description += f"- ... and {len(self.endpoints) - 5} more endpoints\n"

        description += "\nThis tool includes enterprise safety controls and HITL approval for high-risk operations."

        return description

    def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information and status.

        Returns:
            Dictionary with tool information
        """
        return {
            "tool_name": self.tool_name,
            "is_initialized": self.is_initialized,
            "base_url": self.base_url,
            "endpoint_count": len(self.endpoints),
            "security_schemes": list(self.security_schemes.keys()),
            "adk_tool_available": self.adk_tool is not None
        }
