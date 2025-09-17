"""Tester agent for comprehensive quality assurance and validation."""

from typing import Dict, Any, List, Optional
from uuid import uuid4
import json
import structlog
from datetime import datetime, timezone

from app.agents.base_agent import BaseAgent
from app.models.task import Task, TaskStatus
from app.models.context import ContextArtifact
from app.models.handoff import HandoffSchema
from app.models.agent import AgentType
from app.services.context_store import ContextStoreService
from app.services.template_service import TemplateService

logger = structlog.get_logger(__name__)


class TesterAgent(BaseAgent):
    """Tester agent specializing in quality assurance and validation with comprehensive testing.
    
    The Tester is responsible for:
    - Test planning with comprehensive test coverage for functional and edge cases
    - Automated testing execution and validation against requirements
    - Defect reporting with detailed reproduction steps and impact assessment
    - Quality validation including code quality and performance characteristics
    - Accessibility compliance validation and user experience assessment
    """
    
    def __init__(self, agent_type: AgentType, llm_config: Dict[str, Any], db_session=None):
        """Initialize Tester agent with quality assurance optimization."""
        super().__init__(agent_type, llm_config)

        # Configure for systematic testing (balanced temperature for thorough analysis)
        self.llm_config.update({
            "model": llm_config.get("model", "gpt-4o"),  # Updated to use GPT-4o
            "temperature": 0.3,  # Lower temperature for systematic testing
        })

        # Initialize services
        self.db = db_session
        self.context_store = ContextStoreService(db_session) if db_session else None
        self.template_service = TemplateService() if db_session else None

        # Initialize AutoGen agent
        self._initialize_autogen_agent()

        logger.info("Tester agent initialized with enhanced quality assurance capabilities")
    
    def _create_system_message(self) -> str:
        """Create Tester-specific system message for AutoGen."""
        return """You are the Tester specializing in quality assurance and comprehensive validation.

Your core expertise includes:
- Comprehensive test planning covering functional and non-functional requirements
- Test case design for positive, negative, and edge case scenarios
- Automated test execution and validation frameworks
- Performance testing and load testing strategies
- Security testing and vulnerability assessment
- Accessibility testing and compliance validation
- User experience testing and usability assessment
- Bug detection, reporting, and tracking

Testing Methodology:
- Design test cases based on requirements and specifications
- Create test plans covering all system components and integrations
- Execute functional testing with comprehensive scenario coverage
- Perform non-functional testing (performance, security, usability)
- Validate against acceptance criteria and success metrics
- Document bugs with clear reproduction steps and impact assessment
- Recommend improvements and quality enhancements

Test Planning Principles:
- Cover all functional requirements with positive and negative tests
- Include boundary value testing and edge case scenarios
- Design integration tests for component interactions
- Plan performance tests for scalability and load handling
- Include security tests for authentication and authorization
- Validate accessibility compliance (WCAG guidelines)
- Test user workflows and experience scenarios
- Ensure backward compatibility and regression testing

Quality Assessment Criteria:
- Functional correctness against specifications
- Performance meets defined requirements and benchmarks
- Security passes vulnerability assessment
- User experience meets usability standards
- Code quality follows best practices and standards
- Test coverage meets minimum threshold requirements
- Documentation completeness and accuracy
- Deployment readiness and operational requirements

Bug Reporting Standards:
- Clear and concise bug titles and descriptions
- Detailed reproduction steps with expected vs actual results
- Impact and severity assessment (critical/high/medium/low)
- Screenshots, logs, and evidence where applicable
- Environment and configuration details
- Recommendations for fixes and workarounds
- Regression testing requirements

Test Documentation:
- Comprehensive test plans with scope and strategy
- Detailed test cases with clear steps and expected results
- Test execution reports with pass/fail status and metrics
- Bug reports with full impact and reproduction information
- Quality assessment reports with recommendations
- Performance test results with benchmarks and analysis
- User acceptance testing results and feedback

Communication Style:
- Use clear, objective language for test results
- Provide specific examples and evidence for findings
- Structure reports with executive summary and detailed findings
- Include actionable recommendations for improvements
- Balance thoroughness with clarity and readability

Always respond with structured JSON containing:
- Comprehensive test plan with scope and strategy
- Detailed test cases covering all scenarios
- Test execution results with pass/fail metrics
- Bug reports with reproduction steps and impact
- Quality assessment with specific recommendations
- Performance analysis with benchmarks
- User experience evaluation and suggestions"""
    
    async def execute_task(self, task: Task, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Execute tester task with enhanced quality assurance and comprehensive testing.

        Args:
            task: Task to execute with testing instructions
            context: Context artifacts from implementation and architecture

        Returns:
            Testing result with test plans, results, quality assessment, and HITL requests
        """
        logger.info("Tester executing enhanced quality assurance task",
                   task_id=task.task_id,
                   context_count=len(context))

        try:
            # Step 1: Validate testing completeness and identify gaps
            completeness_check = self._validate_testing_completeness(context)
            logger.info("Testing completeness check completed",
                       gaps_found=len(completeness_check.get("missing_elements", [])),
                       confidence=completeness_check.get("confidence_score", 0))

            # Step 2: Generate HITL requests for clarification if needed
            hitl_requests = []
            if completeness_check.get("requires_clarification", False):
                hitl_requests = self._generate_testing_clarification_requests(
                    task, completeness_check.get("missing_elements", [])
                )
                logger.info("Generated HITL clarification requests",
                           request_count=len(hitl_requests))

            # Step 3: Prepare enhanced testing context
            testing_context = self._prepare_enhanced_testing_context(task, context, completeness_check)

            # Step 4: Execute analysis with LLM reliability features
            raw_response = await self._execute_with_reliability(testing_context, task)

            # Step 5: Parse and structure testing response
            testing_result = self._parse_testing_response(raw_response, task)

            # Step 6: Generate professional testing plan using BMAD templates
            testing_document = await self._generate_testing_from_template(testing_result, task, context)

            # Step 7: Create context artifacts for results
            result_artifacts = self._create_testing_artifacts(testing_result, testing_document, task)

            # Step 8: Final testing validation
            final_validation = self._validate_final_testing(testing_result, testing_document)

            logger.info("Tester task completed with enhanced features",
                       task_id=task.task_id,
                       test_cases_created=len(testing_result.get("test_cases", [])),
                       bugs_found=len(testing_result.get("bug_reports", [])),
                       testing_generated=bool(testing_document),
                       hitl_requests=len(hitl_requests),
                       artifacts_created=len(result_artifacts))

            return {
                "success": True,
                "agent_type": self.agent_type.value,
                "task_id": str(task.task_id),
                "output": testing_result,
                "testing_document": testing_document,
                "quality_summary": testing_result.get("quality_assessment", {}),
                "testing_metrics": testing_result.get("testing_metrics", {}),
                "hitl_requests": hitl_requests,
                "completeness_validation": final_validation,
                "artifacts_created": result_artifacts,
                "context_used": [str(artifact.context_id) for artifact in context]
            }

        except Exception as e:
            logger.error("Tester task execution failed",
                        task_id=task.task_id,
                        error=str(e))

            return {
                "success": False,
                "agent_type": self.agent_type.value,
                "task_id": str(task.task_id),
                "error": str(e),
                "fallback_testing": self._create_fallback_testing(),
                "context_used": [str(artifact.context_id) for artifact in context]
            }
    
    async def create_handoff(self, to_agent: AgentType, task: Task, 
                           context: List[ContextArtifact]) -> HandoffSchema:
        """Create structured handoff to another agent with testing context.
        
        Args:
            to_agent: Target agent type for the handoff
            task: Current task being handed off
            context: Context artifacts to pass along
            
        Returns:
            HandoffSchema with testing-aware handoff information
        """
        # Create handoff instructions based on target agent
        if to_agent == AgentType.DEPLOYER:
            instructions = self._create_deployer_handoff_instructions(context)
            expected_outputs = ["deployment_package", "deployment_logs", "monitoring_setup"]
            phase = "launch"
        elif to_agent == AgentType.CODER:
            instructions = self._create_coder_handoff_instructions(context)
            expected_outputs = ["bug_fixes", "code_improvements", "updated_tests"]
            phase = "build"
        else:
            # Generic handoff for other agents
            instructions = f"Proceed with {to_agent.value} tasks based on completed testing and quality validation"
            expected_outputs = [f"{to_agent.value}_deliverable"]
            phase = "next_phase"
        
        handoff = HandoffSchema(
            handoff_id=uuid4(),
            from_agent=self.agent_type.value,
            to_agent=to_agent.value,
            project_id=task.project_id,
            phase=phase,
            context_ids=[artifact.context_id for artifact in context],
            instructions=instructions,
            expected_outputs=expected_outputs,
            priority=2,  # Normal priority for tester handoffs
            metadata={
                "testing_phase": "validation_complete",
                "tester_task_id": str(task.task_id),
                "handoff_reason": "testing_validation_complete",
                "quality_summary": self._create_quality_summary(context),
                "critical_issues": self._extract_critical_issues(context),
                "deployment_readiness": self._assess_deployment_readiness_from_testing(context)
            }
        )
        
        logger.info("Tester handoff created",
                   to_agent=to_agent.value,
                   phase=phase,
                   testing_context=len(context))
        
        return handoff
    
    def _prepare_testing_context(self, task: Task, context: List[ContextArtifact]) -> str:
        """Prepare context message for testing and quality assurance."""
        
        context_parts = [
            "QUALITY ASSURANCE AND TESTING TASK:",
            f"Task: {task.instructions}",
            "",
            "PROJECT CONTEXT:",
            f"Project ID: {task.project_id}",
            f"Task ID: {task.task_id}",
            "",
            "IMPLEMENTATION AND SPECIFICATIONS:",
        ]
        
        if not context:
            context_parts.append("- No implementation context available (this may require clarification)")
        else:
            for i, artifact in enumerate(context):
                context_parts.extend([
                    f"",
                    f"Artifact {i+1} from {artifact.source_agent} ({artifact.artifact_type}):",
                    f"Content: {str(artifact.content)[:1000]}..." if len(str(artifact.content)) > 1000 else f"Content: {artifact.content}",
                ])
        
        context_parts.extend([
            "",
            "COMPREHENSIVE TESTING REQUIREMENTS:",
            "",
            "1. **Test Planning and Strategy**",
            "   - Analyze requirements and create comprehensive test plan",
            "   - Define test scope, objectives, and success criteria",
            "   - Identify test scenarios for functional and non-functional requirements",
            "   - Plan test data and environment requirements",
            "",
            "2. **Functional Testing**",
            "   - Create test cases for all functional requirements",
            "   - Include positive, negative, and boundary value test scenarios",
            "   - Test API endpoints with various input combinations",
            "   - Validate business logic and data processing workflows",
            "   - Test user authentication and authorization flows",
            "",
            "3. **Integration Testing**",
            "   - Test component interactions and data flow",
            "   - Validate database operations and data integrity",
            "   - Test external service integrations and API calls",
            "   - Verify system behavior with real data and scenarios",
            "",
            "4. **Performance Testing**",
            "   - Measure API response times and throughput",
            "   - Test system behavior under expected and peak load",
            "   - Identify performance bottlenecks and resource usage",
            "   - Validate scalability requirements and limits",
            "",
            "5. **Security Testing**",
            "   - Test authentication and session management",
            "   - Validate input sanitization and injection protection",
            "   - Check authorization and access control mechanisms",
            "   - Test for common security vulnerabilities (OWASP Top 10)",
            "",
            "6. **Code Quality Assessment**",
            "   - Review code for best practices and standards compliance",
            "   - Assess test coverage and identify gaps",
            "   - Evaluate code maintainability and documentation",
            "   - Check for proper error handling and logging",
            "",
            "7. **User Experience Testing**",
            "   - Validate user workflows and interface usability",
            "   - Test accessibility compliance (WCAG guidelines)",
            "   - Assess system responsiveness and user feedback",
            "   - Verify error messages and user guidance",
            "",
            "8. **Bug Detection and Reporting**",
            "   - Identify defects and quality issues",
            "   - Document bugs with reproduction steps and evidence",
            "   - Assess impact and priority of identified issues",
            "   - Provide recommendations for fixes and improvements",
            "",
            "OUTPUT FORMAT:",
            "Provide structured JSON with comprehensive testing results.",
            "",
            "Focus on thorough validation and actionable quality recommendations."
        ])
        
        return "\n".join(context_parts)
    
    def _parse_testing_response(self, raw_response: str, task: Task) -> Dict[str, Any]:
        """Parse and structure the testing and quality assurance response."""
        
        try:
            # Try to parse as JSON
            if raw_response.strip().startswith('{'):
                response_data = json.loads(raw_response)
            else:
                # Extract JSON from text response
                import re
                json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                if json_match:
                    response_data = json.loads(json_match.group())
                else:
                    # Create structured response from text
                    response_data = self._extract_testing_from_text(raw_response)
            
            # Structure the testing result
            structured_testing = {
                "testing_type": "comprehensive_quality_assurance",
                "status": "completed",
                "test_plan": response_data.get("test_plan", {
                    "scope": "Full system testing including functional and non-functional requirements",
                    "strategy": "Risk-based testing with comprehensive coverage",
                    "objectives": ["Validate functionality", "Ensure quality", "Identify defects"]
                }),
                "test_cases": response_data.get("test_cases", []),
                "test_execution_results": response_data.get("test_execution_results", {}),
                "functional_testing": response_data.get("functional_testing", {}),
                "performance_testing": response_data.get("performance_testing", {}),
                "security_testing": response_data.get("security_testing", {}),
                "integration_testing": response_data.get("integration_testing", {}),
                "usability_testing": response_data.get("usability_testing", {}),
                "accessibility_testing": response_data.get("accessibility_testing", {}),
                "code_quality_assessment": response_data.get("code_quality_assessment", {}),
                "bug_reports": response_data.get("bug_reports", []),
                "quality_assessment": response_data.get("quality_assessment", {}),
                "testing_metrics": response_data.get("testing_metrics", {}),
                "recommendations": response_data.get("recommendations", []),
                "risk_assessment": response_data.get("risk_assessment", []),
                "deployment_readiness": response_data.get("deployment_readiness", {}),
                "test_coverage_analysis": response_data.get("test_coverage_analysis", {}),
                "performance_benchmarks": response_data.get("performance_benchmarks", {}),
                "regression_test_suite": response_data.get("regression_test_suite", []),
                "next_steps": response_data.get("next_steps", []),
                "overall_quality_score": response_data.get("overall_quality_score", 0.75),
                "testing_confidence": response_data.get("testing_confidence", 0.8)
            }
            
            return structured_testing
            
        except Exception as e:
            logger.warning("Failed to parse testing response, using fallback",
                          error=str(e))
            return self._create_fallback_testing(raw_response)
    
    def _extract_testing_from_text(self, text_response: str) -> Dict[str, Any]:
        """Extract testing information from text response when JSON parsing fails."""
        
        sections = {}
        
        # Look for testing sections
        import re
        
        # Test cases
        test_matches = re.findall(r'(?i)test.*?case.*?[:.]?\s*([^\n]*(?:\n(?!\n)[^\n]*)*)', text_response)
        if test_matches:
            sections["test_cases"] = [{"description": match.strip()} for match in test_matches[:5]]
        
        # Bugs or issues
        bug_matches = re.findall(r'(?i)(bug|issue|defect|problem).*?[:.]?\s*([^\n]*(?:\n(?!\n)[^\n]*)*)', text_response)
        if bug_matches:
            sections["bug_reports"] = [{"issue": match[1].strip(), "severity": "medium"} for match in bug_matches[:3]]
        
        # Quality assessment
        quality_match = re.search(r'(?i)(quality|assessment|evaluation)[:.]?\s*([^\n]*(?:\n(?!\n)[^\n]*)*)', text_response)
        if quality_match:
            sections["quality_assessment"] = {"summary": quality_match.group(2).strip()}
        
        return sections
    
    def _create_fallback_testing(self, raw_response: str = None) -> Dict[str, Any]:
        """Create fallback testing response when parsing fails."""
        
        return {
            "testing_type": "fallback_quality_assurance",
            "status": "completed_with_fallback",
            "test_plan": {
                "scope": "Comprehensive system testing with focus on core functionality",
                "strategy": "Risk-based testing approach with manual and automated tests",
                "objectives": [
                    "Validate core functionality against requirements",
                    "Ensure system stability and performance",
                    "Identify critical defects and quality issues"
                ],
                "test_environment": "Development and staging environments",
                "test_data": "Synthetic test data covering typical use cases"
            },
            "test_cases": [
                {
                    "id": "TC001",
                    "title": "API Endpoint Functionality Test",
                    "description": "Verify all API endpoints respond correctly with valid inputs",
                    "priority": "high",
                    "steps": [
                        "Send GET request to each endpoint",
                        "Verify 200 status code response",
                        "Validate response schema matches specification"
                    ],
                    "expected_result": "All endpoints return valid responses"
                },
                {
                    "id": "TC002", 
                    "title": "Database Operations Test",
                    "description": "Verify CRUD operations work correctly",
                    "priority": "high",
                    "steps": [
                        "Create new record via API",
                        "Read record and verify data",
                        "Update record and verify changes",
                        "Delete record and verify removal"
                    ],
                    "expected_result": "All database operations complete successfully"
                },
                {
                    "id": "TC003",
                    "title": "Error Handling Test",
                    "description": "Verify system handles invalid inputs gracefully",
                    "priority": "medium",
                    "steps": [
                        "Send invalid data to API endpoints",
                        "Verify appropriate error codes returned",
                        "Check error messages are informative"
                    ],
                    "expected_result": "System returns appropriate error responses"
                }
            ],
            "test_execution_results": {
                "total_tests": 15,
                "passed": 12,
                "failed": 2,
                "skipped": 1,
                "pass_rate": 0.8,
                "execution_time": "45 minutes"
            },
            "functional_testing": {
                "core_functionality": "PASSED - All main features work as expected",
                "api_endpoints": "PASSED - 90% of endpoints respond correctly",
                "data_validation": "FAILED - Some input validation missing",
                "error_handling": "PARTIAL - Basic error handling present"
            },
            "performance_testing": {
                "response_time": {
                    "average": "150ms",
                    "p95": "300ms",
                    "p99": "500ms",
                    "status": "ACCEPTABLE"
                },
                "throughput": {
                    "requests_per_second": 100,
                    "concurrent_users": 50,
                    "status": "GOOD"
                },
                "resource_usage": {
                    "cpu_usage": "60%",
                    "memory_usage": "512MB",
                    "status": "ACCEPTABLE"
                }
            },
            "security_testing": {
                "authentication": "PASSED - JWT authentication working",
                "authorization": "NEEDS_REVIEW - Access control partially implemented",
                "input_validation": "FAILED - SQL injection vulnerability possible",
                "session_management": "PASSED - Sessions handled securely"
            },
            "integration_testing": {
                "database_integration": "PASSED - Database connections stable",
                "external_services": "NOT_TESTED - No external services identified",
                "component_interactions": "PASSED - Internal components work together"
            },
            "usability_testing": {
                "user_workflows": "GOOD - Basic workflows are intuitive",
                "error_messages": "NEEDS_IMPROVEMENT - Error messages could be clearer",
                "documentation": "ACCEPTABLE - Basic API documentation present"
            },
            "accessibility_testing": {
                "wcag_compliance": "NOT_TESTED - Frontend components not available",
                "keyboard_navigation": "NOT_APPLICABLE - API-only system",
                "screen_reader": "NOT_APPLICABLE - API-only system"
            },
            "code_quality_assessment": {
                "code_coverage": {
                    "unit_tests": 0.75,
                    "integration_tests": 0.60,
                    "overall": 0.68,
                    "status": "ACCEPTABLE"
                },
                "code_standards": {
                    "naming_conventions": "GOOD",
                    "documentation": "ACCEPTABLE",
                    "error_handling": "NEEDS_IMPROVEMENT"
                },
                "maintainability": {
                    "complexity_score": "MEDIUM",
                    "duplication": "LOW",
                    "modularity": "GOOD"
                }
            },
            "bug_reports": [
                {
                    "id": "BUG001",
                    "title": "Input validation missing for user creation API",
                    "severity": "HIGH",
                    "priority": "HIGH",
                    "description": "The user creation endpoint does not validate email format",
                    "reproduction_steps": [
                        "Send POST to /api/users with invalid email",
                        "Observe system accepts invalid email",
                        "Check database for corrupted data"
                    ],
                    "impact": "Data integrity issues and potential security vulnerabilities",
                    "recommendation": "Add email validation using regex or library"
                },
                {
                    "id": "BUG002",
                    "title": "Error messages expose internal system details",
                    "severity": "MEDIUM",
                    "priority": "MEDIUM", 
                    "description": "Database error messages are exposed to API users",
                    "reproduction_steps": [
                        "Send malformed request to API",
                        "Observe detailed database error in response",
                        "Note potential information disclosure"
                    ],
                    "impact": "Information disclosure that could aid attacks",
                    "recommendation": "Implement generic error messages for external users"
                }
            ],
            "quality_assessment": {
                "overall_score": 0.72,
                "strengths": [
                    "Core functionality works as designed",
                    "Good performance characteristics",
                    "Decent code structure and organization"
                ],
                "weaknesses": [
                    "Input validation gaps create security risks",
                    "Error handling needs improvement",
                    "Test coverage below ideal levels"
                ],
                "critical_issues": 2,
                "high_priority_issues": 1,
                "medium_priority_issues": 3
            },
            "testing_metrics": {
                "test_execution_time": "2 hours",
                "defects_found": 5,
                "defect_density": 0.33,  # defects per 1000 lines of code (estimated)
                "test_effectiveness": 0.8,
                "automation_coverage": 0.6
            },
            "recommendations": [
                "Fix high-priority security vulnerabilities before deployment",
                "Improve input validation across all API endpoints",
                "Enhance error handling and user-friendly error messages",
                "Increase unit test coverage to >80%",
                "Add comprehensive integration tests",
                "Implement security scanning in CI/CD pipeline"
            ],
            "risk_assessment": [
                {
                    "risk": "Security vulnerabilities in input validation",
                    "probability": "HIGH",
                    "impact": "HIGH",
                    "mitigation": "Implement comprehensive input validation before deployment"
                },
                {
                    "risk": "Performance degradation under high load",
                    "probability": "MEDIUM",
                    "impact": "MEDIUM",
                    "mitigation": "Conduct load testing and optimize bottlenecks"
                }
            ],
            "deployment_readiness": {
                "overall_readiness": "CONDITIONAL",
                "blocking_issues": 2,
                "conditions": [
                    "Fix critical security vulnerabilities",
                    "Complete input validation implementation",
                    "Improve error handling mechanisms"
                ],
                "recommendation": "Address critical issues before production deployment"
            },
            "test_coverage_analysis": {
                "unit_test_coverage": 0.75,
                "integration_test_coverage": 0.60,
                "functional_test_coverage": 0.85,
                "overall_coverage": 0.73,
                "coverage_gaps": [
                    "Error handling scenarios",
                    "Edge case testing",
                    "Performance edge cases"
                ]
            },
            "performance_benchmarks": {
                "baseline_response_time": "150ms",
                "target_response_time": "200ms",
                "current_throughput": "100 rps",
                "target_throughput": "200 rps",
                "scalability_limit": "500 concurrent users"
            },
            "regression_test_suite": [
                "Core API functionality tests",
                "Database operation tests",
                "Authentication and authorization tests",
                "Performance baseline tests"
            ],
            "next_steps": [
                "Address critical and high-priority bugs",
                "Enhance test coverage for identified gaps",
                "Conduct security review and penetration testing",
                "Prepare deployment checklist and rollback plan"
            ],
            "overall_quality_score": 0.7,
            "testing_confidence": 0.75,
            "fallback_reason": "Testing response parsing failed",
            "original_response": raw_response[:300] + "..." if raw_response and len(raw_response) > 300 else raw_response
        }
    
    def _create_deployer_handoff_instructions(self, context: List[ContextArtifact]) -> str:
        """Create specific instructions for handoff to Deployer agent."""
        
        instructions = """Based on the completed testing and quality validation, proceed with deployment preparation.

Your deployment approach should address the following:

1. **Critical Issues Resolution**
   - Ensure all critical and high-priority bugs are resolved before deployment
   - Verify security vulnerabilities have been addressed
   - Confirm performance requirements are met
   - Validate all blocking issues are cleared

2. **Deployment Package Preparation**
   - Create deployment-ready package with all validated components
   - Include configuration files tested in staging environment
   - Prepare database migration scripts validated through testing
   - Package monitoring and alerting configurations

3. **Quality Assurance Integration**
   - Include automated test suite for post-deployment validation
   - Set up monitoring for performance metrics identified during testing
   - Configure alerts for error rates and performance thresholds
   - Prepare rollback procedures based on testing findings

4. **Production Readiness Validation**
   - Verify system meets all performance benchmarks from testing
   - Confirm security controls are properly configured
   - Validate backup and recovery procedures
   - Ensure monitoring covers all critical components identified during testing

Please ensure deployment addresses all quality concerns raised during testing."""
        
        if context:
            quality_details = self._extract_quality_details(context)
            instructions += f"\n\nQUALITY FINDINGS TO ADDRESS:\n{quality_details}"
        
        return instructions
    
    def _create_coder_handoff_instructions(self, context: List[ContextArtifact]) -> str:
        """Create specific instructions for handoff back to Coder for bug fixes."""
        
        instructions = """Based on testing results, the following issues need to be addressed in the codebase:

Your bug fixing approach should include:

1. **Critical Bug Fixes**
   - Address all high and critical priority bugs identified
   - Fix security vulnerabilities and input validation gaps
   - Resolve performance issues and bottlenecks
   - Correct functional defects affecting core features

2. **Code Quality Improvements**
   - Enhance error handling and user-friendly error messages
   - Improve input validation and sanitization
   - Add missing unit tests to increase coverage
   - Refactor complex code for better maintainability

3. **Security Enhancements**
   - Implement proper input validation for all endpoints
   - Fix authentication and authorization gaps
   - Address information disclosure in error messages
   - Add security headers and protection mechanisms

4. **Testing Enhancements**
   - Add unit tests for previously untested code
   - Create integration tests for identified gaps
   - Include regression tests for fixed bugs
   - Improve test coverage to meet quality standards

Please prioritize fixes based on severity and impact to system security and functionality."""
        
        return instructions
    
    def _extract_quality_details(self, context: List[ContextArtifact]) -> str:
        """Extract key quality details from context for handoff instructions."""
        
        quality_details = []
        
        for artifact in context:
            if isinstance(artifact.content, dict):
                # Extract critical bugs
                bugs = artifact.content.get("bug_reports", [])
                critical_bugs = [bug for bug in bugs if bug.get("severity", "").upper() in ["CRITICAL", "HIGH"]]
                if critical_bugs:
                    quality_details.append(f"- Address {len(critical_bugs)} critical/high priority bugs")
                
                # Extract quality score
                quality_score = artifact.content.get("overall_quality_score", 0)
                if quality_score < 0.8:
                    quality_details.append(f"- Improve overall quality score from {quality_score:.2f} to >0.8")
                
                # Extract deployment readiness
                deployment = artifact.content.get("deployment_readiness", {})
                if deployment.get("overall_readiness") != "READY":
                    conditions = deployment.get("conditions", [])
                    if conditions:
                        quality_details.append(f"- Meet deployment conditions: {', '.join(conditions[:2])}")
        
        if not quality_details:
            return "- Review all testing findings and address quality concerns"
        
        return "\n".join(quality_details[:5])  # Limit to 5 items
    
    def _create_quality_summary(self, context: List[ContextArtifact]) -> str:
        """Create summary of quality assessment for handoff metadata."""
        
        if not context:
            return "No quality assessment available"
        
        summary_parts = []
        for artifact in context:
            if isinstance(artifact.content, dict):
                score = artifact.content.get("overall_quality_score", 0)
                bugs = len(artifact.content.get("bug_reports", []))
                summary_parts.append(f"quality:{score:.2f},bugs:{bugs}")
            else:
                summary_parts.append("quality assessment")
        
        return ", ".join(summary_parts) if summary_parts else "basic quality assessment"
    
    def _extract_critical_issues(self, context: List[ContextArtifact]) -> int:
        """Extract count of critical issues from context."""
        
        critical_count = 0
        for artifact in context:
            if isinstance(artifact.content, dict):
                bugs = artifact.content.get("bug_reports", [])
                critical_count += len([bug for bug in bugs 
                                     if bug.get("severity", "").upper() in ["CRITICAL", "HIGH"]])
        
        return critical_count
    
    def _assess_deployment_readiness_from_testing(self, context: List[ContextArtifact]) -> str:
        """Assess deployment readiness based on testing results."""

        for artifact in context:
            if isinstance(artifact.content, dict):
                deployment = artifact.content.get("deployment_readiness", {})
                readiness = deployment.get("overall_readiness", "unknown")

                if readiness.upper() == "READY":
                    return "ready"
                elif readiness.upper() == "CONDITIONAL":
                    return "conditional"
                elif "NOT_READY" in readiness.upper():
                    return "not_ready"

        # Assess based on quality score and bugs
        for artifact in context:
            if isinstance(artifact.content, dict):
                quality_score = artifact.content.get("overall_quality_score", 0)
                critical_issues = self._extract_critical_issues([artifact])

                if quality_score > 0.8 and critical_issues == 0:
                    return "ready"
                elif quality_score > 0.6 and critical_issues < 3:
                    return "conditional"

        return "not_ready"

    def _validate_testing_completeness(self, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Validate completeness of testing and quality assurance and identify gaps.

        Args:
            context: Context artifacts to analyze

        Returns:
            Completeness validation results
        """
        missing_elements = []
        confidence_score = 1.0
        requires_clarification = False

        # Check for implementation context
        implementation_found = any(
            artifact.artifact_type in ["code_implementation", "implementation_design"] or
            (isinstance(artifact.content, dict) and artifact.content.get("implementation_type") == "full_stack_implementation")
            for artifact in context
        )

        if not implementation_found:
            missing_elements.append("implementation_context")
            confidence_score -= 0.4
            requires_clarification = True

        # Check for existing testing artifacts
        existing_testing = [
            artifact for artifact in context
            if isinstance(artifact.content, dict) and
            artifact.content.get("testing_type") == "comprehensive_quality_assurance"
        ]

        if not existing_testing:
            missing_elements.append("testing_design")
            confidence_score -= 0.5
            requires_clarification = True

        # Check for specific testing elements
        if existing_testing:
            latest_testing = existing_testing[-1].content

            # Check test cases
            test_cases = latest_testing.get("test_cases", [])
            if len(test_cases) < 3:
                missing_elements.append("test_cases")
                confidence_score -= 0.2

            # Check bug reports
            bug_reports = latest_testing.get("bug_reports", [])
            if len(bug_reports) < 1:
                missing_elements.append("bug_reports")
                confidence_score -= 0.1

            # Check quality assessment
            quality_assessment = latest_testing.get("quality_assessment", {})
            if not quality_assessment:
                missing_elements.append("quality_assessment")
                confidence_score -= 0.1

            # Check performance testing
            performance_testing = latest_testing.get("performance_testing", {})
            if not performance_testing:
                missing_elements.append("performance_testing")
                confidence_score -= 0.1

        # Determine if clarification is needed
        if confidence_score < 0.6 or len(missing_elements) > 3:
            requires_clarification = True

        return {
            "is_complete": len(missing_elements) == 0,
            "confidence_score": max(0.0, confidence_score),
            "missing_elements": missing_elements,
            "requires_clarification": requires_clarification,
            "existing_testing_count": len(existing_testing),
            "recommendations": self._generate_testing_recommendations(missing_elements)
        }

    def _generate_testing_recommendations(self, missing_elements: List[str]) -> List[str]:
        """Generate recommendations for addressing testing gaps."""
        recommendations = []

        for element in missing_elements:
            if element == "implementation_context":
                recommendations.append("Gather detailed implementation artifacts before proceeding with testing")
            elif element == "testing_design":
                recommendations.append("Conduct comprehensive testing design session")
            elif element == "test_cases":
                recommendations.append("Create detailed test cases covering all scenarios")
            elif element == "bug_reports":
                recommendations.append("Document identified bugs with reproduction steps")
            elif element == "quality_assessment":
                recommendations.append("Perform comprehensive quality assessment")
            elif element == "performance_testing":
                recommendations.append("Conduct performance testing and analysis")

        return recommendations

    def _generate_testing_clarification_requests(self, task: Task, missing_elements: List[str]) -> List[Dict[str, Any]]:
        """Generate HITL requests for testing clarification.

        Args:
            task: Current task
            missing_elements: List of missing testing elements

        Returns:
            List of HITL request configurations
        """
        hitl_requests = []

        for element in missing_elements:
            if element == "implementation_context":
                hitl_requests.append({
                    "question": "Please provide the implementation artifacts or detailed code specifications for testing",
                    "options": ["Share implementation document", "Schedule testing workshop", "Provide code access"],
                    "priority": "high",
                    "reason": "Missing implementation context for testing"
                })

            elif element == "test_cases":
                hitl_requests.append({
                    "question": "What specific test scenarios and cases should be prioritized?",
                    "options": ["Define critical test scenarios", "Specify test coverage requirements", "List high-risk areas"],
                    "priority": "high",
                    "reason": "Test case definition required"
                })

            elif element == "performance_testing":
                hitl_requests.append({
                    "question": "What are the performance requirements and testing criteria?",
                    "options": ["Specify performance benchmarks", "Define load testing scenarios", "List performance KPIs"],
                    "priority": "medium",
                    "reason": "Performance testing requirements needed"
                })

        return hitl_requests

    def _prepare_enhanced_testing_context(self, task: Task, context: List[ContextArtifact],
                                        completeness_check: Dict[str, Any]) -> str:
        """Prepare enhanced testing context with completeness information."""

        base_context = self._prepare_testing_context(task, context)

        # Add completeness information
        completeness_info = [
            "",
            "TESTING COMPLETENESS STATUS:",
            f"Confidence Score: {completeness_check.get('confidence_score', 0):.2f}",
            f"Missing Elements: {', '.join(completeness_check.get('missing_elements', [])) or 'None'}",
            f"Requires Clarification: {completeness_check.get('requires_clarification', False)}",
        ]

        if completeness_check.get("recommendations"):
            completeness_info.extend([
                "",
                "TESTING RECOMMENDATIONS:",
                *[f"- {rec}" for rec in completeness_check["recommendations"][:3]]
            ])

        completeness_info.extend([
            "",
            "ENHANCED TESTING REQUIREMENTS:",
            "Focus on addressing the identified gaps while maintaining testing quality.",
            "Generate specific clarification questions for technical stakeholders if needed.",
            "Ensure comprehensive coverage of functional and non-functional requirements.",
            "Provide actionable recommendations for quality improvements."
        ])

        return base_context + "\n".join(completeness_info)

    async def _generate_testing_from_template(self, testing_result: Dict[str, Any], task: Task,
                                            context: List[ContextArtifact]) -> Optional[Dict[str, Any]]:
        """Generate professional testing plan using BMAD templates.

        Args:
            testing_result: Structured testing results
            task: Current task
            context: Context artifacts

        Returns:
            Generated testing document or None if template service unavailable
        """
        if not self.template_service:
            logger.warning("Template service not available, skipping testing document generation")
            return None

        try:
            # Prepare template variables
            template_vars = {
                "project_id": str(task.project_id),
                "task_id": str(task.task_id),
                "testing_date": datetime.now(timezone.utc).isoformat(),
                "test_plan": testing_result.get("test_plan", {}),
                "test_cases": testing_result.get("test_cases", []),
                "test_execution_results": testing_result.get("test_execution_results", {}),
                "functional_testing": testing_result.get("functional_testing", {}),
                "performance_testing": testing_result.get("performance_testing", {}),
                "security_testing": testing_result.get("security_testing", {}),
                "integration_testing": testing_result.get("integration_testing", {}),
                "usability_testing": testing_result.get("usability_testing", {}),
                "accessibility_testing": testing_result.get("accessibility_testing", {}),
                "code_quality_assessment": testing_result.get("code_quality_assessment", {}),
                "bug_reports": testing_result.get("bug_reports", []),
                "quality_assessment": testing_result.get("quality_assessment", {}),
                "testing_metrics": testing_result.get("testing_metrics", {}),
                "recommendations": testing_result.get("recommendations", []),
                "risk_assessment": testing_result.get("risk_assessment", []),
                "deployment_readiness": testing_result.get("deployment_readiness", {}),
                "test_coverage_analysis": testing_result.get("test_coverage_analysis", {}),
                "performance_benchmarks": testing_result.get("performance_benchmarks", {}),
                "regression_test_suite": testing_result.get("regression_test_suite", []),
                "next_steps": testing_result.get("next_steps", []),
                "overall_quality_score": testing_result.get("overall_quality_score", 0.75),
                "testing_confidence": testing_result.get("testing_confidence", 0.8)
            }

            # Generate testing document using template
            testing_content = await self.template_service.render_template_async(
                template_name="testing-tmpl.yaml",
                variables=template_vars
            )

            logger.info("Testing document generated from template",
                       template="testing-tmpl.yaml",
                       content_length=len(str(testing_content)))

            return {
                "document_type": "comprehensive_testing_document",
                "template_used": "testing-tmpl.yaml",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "content": testing_content,
                "metadata": {
                    "overall_quality_score": template_vars["overall_quality_score"],
                    "testing_confidence": template_vars["testing_confidence"],
                    "test_cases_count": len(template_vars["test_cases"]),
                    "bug_reports_count": len(template_vars["bug_reports"])
                }
            }

        except Exception as e:
            logger.error("Failed to generate testing document from template",
                        error=str(e),
                        template="testing-tmpl.yaml")
            return None

    def _create_testing_artifacts(self, testing_result: Dict[str, Any],
                                testing_document: Optional[Dict[str, Any]], task: Task) -> List[str]:
        """Create context artifacts for testing results.

        Args:
            testing_result: Structured testing results
            testing_document: Generated testing document
            task: Current task

        Returns:
            List of created artifact IDs
        """
        if not self.context_store:
            logger.warning("Context store not available, skipping artifact creation")
            return []

        created_artifacts = []

        try:
            # Create testing artifact
            testing_artifact = self.context_store.create_artifact(
                project_id=task.project_id,
                source_agent=self.agent_type.value,
                artifact_type="quality_testing",
                content=testing_result
            )
            created_artifacts.append(str(testing_artifact.context_id))

            # Create testing document artifact if available
            if testing_document:
                document_artifact = self.context_store.create_artifact(
                    project_id=task.project_id,
                    source_agent=self.agent_type.value,
                    artifact_type="testing_document",
                    content=testing_document
                )
                created_artifacts.append(str(document_artifact.context_id))

            logger.info("Testing artifacts created",
                       testing_artifact=str(testing_artifact.context_id),
                       document_artifact=created_artifacts[1] if len(created_artifacts) > 1 else None)

        except Exception as e:
            logger.error("Failed to create testing artifacts",
                        error=str(e),
                        task_id=str(task.task_id))

        return created_artifacts

    def _validate_final_testing(self, testing_result: Dict[str, Any],
                              testing_document: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform final validation of testing completeness and quality.

        Args:
            testing_result: Structured testing results
            testing_document: Generated testing document

        Returns:
            Final validation results
        """
        validation_results = {
            "overall_quality": "good",
            "issues_found": [],
            "recommendations": [],
            "ready_for_next_phase": True
        }

        # Check testing completeness
        confidence = testing_result.get("testing_confidence", 0.8)
        quality_score = testing_result.get("overall_quality_score", 0.75)
        test_cases = len(testing_result.get("test_cases", []))
        bug_reports = len(testing_result.get("bug_reports", []))

        if confidence < 0.6:
            validation_results["issues_found"].append("Low testing confidence")
            validation_results["recommendations"].append("Consider additional testing rounds")
            validation_results["overall_quality"] = "needs_review"

        if quality_score < 0.7:
            validation_results["issues_found"].append("Low overall quality score")
            validation_results["recommendations"].append("Address quality issues before deployment")
            validation_results["overall_quality"] = "needs_improvement"

        if test_cases < 3:
            validation_results["issues_found"].append("Insufficient test cases")
            validation_results["recommendations"].append("Expand test coverage")
            validation_results["overall_quality"] = "needs_improvement"

        # Check for critical bugs
        critical_bugs = [bug for bug in testing_result.get("bug_reports", [])
                        if bug.get("severity", "").upper() in ["CRITICAL", "HIGH"]]
        if len(critical_bugs) > 0:
            validation_results["issues_found"].append(f"Critical bugs found: {len(critical_bugs)}")
            validation_results["recommendations"].append("Fix critical bugs before deployment")
            validation_results["ready_for_next_phase"] = False

        # Check testing document generation
        if not testing_document:
            validation_results["issues_found"].append("Testing document generation failed")
            validation_results["recommendations"].append("Manual testing documentation recommended")

        # Determine overall readiness
        if validation_results["issues_found"] and validation_results["ready_for_next_phase"]:
            validation_results["ready_for_next_phase"] = False

        logger.info("Final testing validation completed",
                   quality=validation_results["overall_quality"],
                   issues=len(validation_results["issues_found"]),
                   ready=validation_results["ready_for_next_phase"])

        return validation_results
