"""Deployer agent for comprehensive deployment automation and production operations."""

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


class DeployerAgent(BaseAgent):
    """Deployer agent specializing in deployment automation and environment management.
    
    The Deployer is responsible for:
    - Deployment automation to target environments (GitHub Codespaces, Vercel)
    - Pipeline configuration including deployment pipelines and environment variables
    - Health validation with deployment success verification and comprehensive checks
    - Documentation creation including deployment docs and rollback procedures
    - Monitoring setup for post-deployment system performance and stability
    """
    
    def __init__(self, agent_type: AgentType, llm_config: Dict[str, Any], db_session=None):
        """Initialize Deployer agent with deployment automation optimization."""
        super().__init__(agent_type, llm_config)

        # Configure for systematic deployment (lower temperature for precision)
        self.llm_config.update({
            "model": llm_config.get("model", "gpt-4o"),  # Updated to use GPT-4o
            "temperature": 0.2,  # Lower temperature for deployment precision
        })

        # Initialize services
        self.db = db_session
        self.context_store = ContextStoreService(db_session) if db_session else None
        self.template_service = TemplateService() if db_session else None

        # Initialize AutoGen agent
        self._initialize_autogen_agent()

        logger.info("Deployer agent initialized with enhanced deployment automation capabilities")
    
    def _create_system_message(self) -> str:
        """Create Deployer-specific system message for AutoGen."""
        return """You are the Deployer specializing in deployment automation and production operations.

Your core expertise includes:
- Deployment automation and CI/CD pipeline configuration
- Infrastructure as Code (IaC) and environment management
- Container orchestration and cloud platform deployment
- Production monitoring and observability setup
- Security configuration and compliance implementation
- Performance optimization and scalability planning
- Incident response and disaster recovery procedures
- DevOps best practices and operational excellence

Deployment Methodology:
- Analyze deployment requirements and target environment constraints
- Design deployment strategy with blue-green or rolling deployment patterns
- Configure CI/CD pipelines with automated testing and quality gates
- Implement infrastructure as code for reproducible deployments
- Set up comprehensive monitoring and alerting systems
- Establish backup and disaster recovery procedures
- Document operational procedures and troubleshooting guides

Environment Management Principles:
- Maintain environment parity (dev/staging/production)
- Implement proper configuration management and secrets handling
- Use containerization for consistent deployment artifacts
- Configure auto-scaling and load balancing for high availability
- Implement proper network security and access controls
- Set up centralized logging and distributed tracing
- Monitor application and infrastructure metrics continuously

Deployment Best Practices:
- Implement zero-downtime deployment strategies
- Use feature flags for gradual rollouts and quick rollbacks
- Automate database migrations with proper rollback procedures
- Configure health checks and readiness probes
- Implement proper error handling and circuit breaker patterns
- Set up automated backup and recovery procedures
- Document deployment procedures and emergency contacts

Security and Compliance:
- Implement proper authentication and authorization
- Configure network security groups and firewalls
- Set up SSL/TLS certificates and secure communication
- Implement secrets management and credential rotation
- Configure audit logging and compliance reporting
- Scan for vulnerabilities and security misconfigurations
- Implement data encryption at rest and in transit

Monitoring and Observability:
- Set up application performance monitoring (APM)
- Configure infrastructure monitoring and alerting
- Implement distributed tracing and log aggregation
- Create operational dashboards and SLA monitoring
- Set up error tracking and exception monitoring
- Configure capacity planning and resource utilization alerts
- Implement synthetic monitoring and uptime checks

Operational Excellence:
- Establish incident response procedures and escalation paths
- Create runbooks for common operational tasks
- Implement automated remediation for known issues
- Set up change management and deployment approval processes
- Configure backup and disaster recovery testing
- Establish performance baselines and SLA targets
- Document operational procedures and knowledge base

Communication Style:
- Use precise technical language with clear step-by-step procedures
- Provide detailed deployment plans with rollback procedures
- Include monitoring and alerting configurations
- Document all decisions with operational rationale
- Structure information for operational handoff
- Include troubleshooting guides and common issues

Always respond with structured JSON containing:
- Comprehensive deployment plan with step-by-step procedures
- Infrastructure configuration and environment setup
- CI/CD pipeline configuration and automation scripts
- Monitoring and alerting setup with specific metrics
- Security configuration and compliance measures
- Operational procedures and troubleshooting guides
- Performance optimization and scalability measures
- Backup and disaster recovery procedures"""
    
    async def execute_task(self, task: Task, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Execute deployer task with enhanced deployment automation and production operations.

        Args:
            task: Task to execute with deployment instructions
            context: Context artifacts from testing and implementation

        Returns:
            Deployment result with configurations, procedures, monitoring setup, and HITL requests
        """
        logger.info("Deployer executing enhanced deployment automation task",
                   task_id=task.task_id,
                   context_count=len(context))

        try:
            # Step 1: Validate deployment completeness and identify gaps
            completeness_check = self._validate_deployment_completeness(context)
            logger.info("Deployment completeness check completed",
                       gaps_found=len(completeness_check.get("missing_elements", [])),
                       confidence=completeness_check.get("confidence_score", 0))

            # Step 2: Generate HITL requests for clarification if needed
            hitl_requests = []
            if completeness_check.get("requires_clarification", False):
                hitl_requests = self._generate_deployment_clarification_requests(
                    task, completeness_check.get("missing_elements", [])
                )
                logger.info("Generated HITL clarification requests",
                           request_count=len(hitl_requests))

            # Step 3: Prepare enhanced deployment context
            deployment_context = self._prepare_enhanced_deployment_context(task, context, completeness_check)

            # Step 4: Execute analysis with LLM reliability features
            raw_response = await self._execute_with_reliability(deployment_context, task)

            # Step 5: Parse and structure deployment response
            deployment_result = self._parse_deployment_response(raw_response, task)

            # Step 6: Generate professional deployment plan using BMAD templates
            deployment_document = await self._generate_deployment_from_template(deployment_result, task, context)

            # Step 7: Create context artifacts for results
            result_artifacts = self._create_deployment_artifacts(deployment_result, deployment_document, task)

            # Step 8: Final deployment validation
            final_validation = self._validate_final_deployment(deployment_result, deployment_document)

            logger.info("Deployer task completed with enhanced features",
                       task_id=task.task_id,
                       environments_configured=len(deployment_result.get("environment_configurations", [])),
                       monitoring_setup=len(deployment_result.get("monitoring_configuration", {})),
                       deployment_generated=bool(deployment_document),
                       hitl_requests=len(hitl_requests),
                       artifacts_created=len(result_artifacts))

            return {
                "success": True,
                "agent_type": self.agent_type.value,
                "task_id": str(task.task_id),
                "output": deployment_result,
                "deployment_document": deployment_document,
                "deployment_summary": deployment_result.get("deployment_overview", {}),
                "operational_procedures": deployment_result.get("operational_procedures", {}),
                "hitl_requests": hitl_requests,
                "completeness_validation": final_validation,
                "artifacts_created": result_artifacts,
                "context_used": [str(artifact.context_id) for artifact in context]
            }

        except Exception as e:
            logger.error("Deployer task execution failed",
                        task_id=task.task_id,
                        error=str(e))

            return {
                "success": False,
                "agent_type": self.agent_type.value,
                "task_id": str(task.task_id),
                "error": str(e),
                "fallback_deployment": self._create_fallback_deployment(),
                "context_used": [str(artifact.context_id) for artifact in context]
            }
    
    async def create_handoff(self, to_agent: AgentType, task: Task, 
                           context: List[ContextArtifact]) -> HandoffSchema:
        """Create structured handoff to another agent with deployment context.
        
        Args:
            to_agent: Target agent type for the handoff
            task: Current task being handed off
            context: Context artifacts to pass along
            
        Returns:
            HandoffSchema with deployment-aware handoff information
        """
        # Create handoff instructions based on target agent
        if to_agent == AgentType.ORCHESTRATOR:
            instructions = self._create_orchestrator_handoff_instructions(context)
            expected_outputs = ["project_completion", "deployment_summary", "operational_handoff"]
            phase = "completed"
        else:
            # Generic handoff for other agents (rare for deployer)
            instructions = f"Proceed with {to_agent.value} tasks based on completed deployment"
            expected_outputs = [f"{to_agent.value}_deliverable"]
            phase = "post_deployment"
        
        handoff = HandoffSchema(
            handoff_id=uuid4(),
            from_agent=self.agent_type.value,
            to_agent=to_agent.value,
            project_id=task.project_id,
            phase=phase,
            context_ids=[artifact.context_id for artifact in context],
            instructions=instructions,
            expected_outputs=expected_outputs,
            priority=1,  # High priority for deployment completion handoffs
            metadata={
                "deployment_phase": "deployment_complete",
                "deployer_task_id": str(task.task_id),
                "handoff_reason": "deployment_complete",
                "deployment_summary": self._create_deployment_summary(context),
                "operational_status": self._extract_operational_status(context),
                "monitoring_active": self._check_monitoring_status(context)
            }
        )
        
        logger.info("Deployer handoff created",
                   to_agent=to_agent.value,
                   phase=phase,
                   deployment_context=len(context))
        
        return handoff
    
    def _prepare_deployment_context(self, task: Task, context: List[ContextArtifact]) -> str:
        """Prepare context message for deployment automation."""
        
        context_parts = [
            "DEPLOYMENT AUTOMATION TASK:",
            f"Task: {task.instructions}",
            "",
            "PROJECT CONTEXT:",
            f"Project ID: {task.project_id}",
            f"Task ID: {task.task_id}",
            "",
            "IMPLEMENTATION AND TESTING CONTEXT:",
        ]
        
        if not context:
            context_parts.append("- No implementation/testing context available (this may require clarification)")
        else:
            for i, artifact in enumerate(context):
                context_parts.extend([
                    f"",
                    f"Artifact {i+1} from {artifact.source_agent} ({artifact.artifact_type}):",
                    f"Content: {str(artifact.content)[:1000]}..." if len(str(artifact.content)) > 1000 else f"Content: {artifact.content}",
                ])
        
        context_parts.extend([
            "",
            "COMPREHENSIVE DEPLOYMENT REQUIREMENTS:",
            "",
            "1. **Deployment Strategy and Planning**",
            "   - Analyze deployment requirements and target environment",
            "   - Design deployment strategy (blue-green, rolling, canary)",
            "   - Create deployment timeline with rollback procedures",
            "   - Plan resource requirements and capacity sizing",
            "",
            "2. **Infrastructure Configuration**",
            "   - Configure target deployment environment (GitHub Codespaces/Vercel)",
            "   - Set up load balancing and auto-scaling configurations",
            "   - Configure network security groups and access controls",
            "   - Implement SSL/TLS certificates and secure communication",
            "",
            "3. **CI/CD Pipeline Setup**",
            "   - Configure automated deployment pipeline",
            "   - Set up quality gates and automated testing integration",
            "   - Implement deployment approval workflows",
            "   - Configure automated rollback triggers",
            "",
            "4. **Application Deployment**",
            "   - Package application for deployment with all dependencies",
            "   - Configure environment variables and secrets management",
            "   - Execute database migrations and schema updates",
            "   - Deploy application with zero-downtime strategy",
            "",
            "5. **Configuration Management**",
            "   - Set up environment-specific configuration files",
            "   - Configure secrets management and credential rotation",
            "   - Implement feature flags for gradual rollouts",
            "   - Set up configuration validation and testing",
            "",
            "6. **Monitoring and Observability**",
            "   - Configure application performance monitoring (APM)",
            "   - Set up infrastructure monitoring and alerting",
            "   - Implement distributed tracing and log aggregation",
            "   - Create operational dashboards and SLA monitoring",
            "",
            "7. **Security Implementation**",
            "   - Configure authentication and authorization systems",
            "   - Implement security scanning and vulnerability management",
            "   - Set up audit logging and compliance reporting",
            "   - Configure data encryption at rest and in transit",
            "",
            "8. **Backup and Disaster Recovery**",
            "   - Configure automated backup procedures",
            "   - Set up disaster recovery and business continuity plans",
            "   - Implement point-in-time recovery capabilities",
            "   - Test backup and recovery procedures",
            "",
            "9. **Health Validation and Testing**",
            "   - Perform post-deployment health checks",
            "   - Execute smoke tests and critical path validation",
            "   - Validate performance against baseline metrics",
            "   - Verify monitoring and alerting functionality",
            "",
            "10. **Operational Documentation**",
            "    - Create deployment runbooks and procedures",
            "    - Document troubleshooting guides and common issues",
            "    - Establish incident response and escalation procedures",
            "    - Create operational handoff documentation",
            "",
            "OUTPUT FORMAT:",
            "Provide structured JSON with comprehensive deployment configuration.",
            "",
            "Focus on production-ready deployment with operational excellence."
        ])
        
        return "\n".join(context_parts)
    
    def _parse_deployment_response(self, raw_response: str, task: Task) -> Dict[str, Any]:
        """Parse and structure the deployment automation response."""
        
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
                    response_data = self._extract_deployment_from_text(raw_response)
            
            # Structure the deployment result
            structured_deployment = {
                "deployment_type": "production_deployment_automation",
                "status": "completed",
                "deployment_overview": response_data.get("deployment_overview", {
                    "strategy": "rolling_deployment",
                    "target_environment": "production",
                    "deployment_time": "estimated_30_minutes"
                }),
                "deployment_plan": response_data.get("deployment_plan", {}),
                "infrastructure_configuration": response_data.get("infrastructure_configuration", {}),
                "environment_configurations": response_data.get("environment_configurations", []),
                "cicd_pipeline": response_data.get("cicd_pipeline", {}),
                "application_deployment": response_data.get("application_deployment", {}),
                "database_deployment": response_data.get("database_deployment", {}),
                "configuration_management": response_data.get("configuration_management", {}),
                "monitoring_configuration": response_data.get("monitoring_configuration", {}),
                "security_configuration": response_data.get("security_configuration", {}),
                "backup_configuration": response_data.get("backup_configuration", {}),
                "health_checks": response_data.get("health_checks", {}),
                "performance_validation": response_data.get("performance_validation", {}),
                "rollback_procedures": response_data.get("rollback_procedures", {}),
                "operational_procedures": response_data.get("operational_procedures", {}),
                "incident_response": response_data.get("incident_response", {}),
                "documentation": response_data.get("documentation", {}),
                "deployment_artifacts": response_data.get("deployment_artifacts", []),
                "post_deployment_tasks": response_data.get("post_deployment_tasks", []),
                "maintenance_procedures": response_data.get("maintenance_procedures", {}),
                "scaling_configuration": response_data.get("scaling_configuration", {}),
                "cost_optimization": response_data.get("cost_optimization", {}),
                "compliance_validation": response_data.get("compliance_validation", {}),
                "deployment_success_rate": response_data.get("deployment_success_rate", 0.95),
                "operational_readiness": response_data.get("operational_readiness", 0.9)
            }
            
            return structured_deployment
            
        except Exception as e:
            logger.warning("Failed to parse deployment response, using fallback",
                          error=str(e))
            return self._create_fallback_deployment(raw_response)
    
    def _extract_deployment_from_text(self, text_response: str) -> Dict[str, Any]:
        """Extract deployment information from text response when JSON parsing fails."""
        
        sections = {}
        
        # Look for deployment sections
        import re
        
        # Deployment steps
        steps_matches = re.findall(r'(?i)(step|deploy|configure).*?[:.]?\s*([^\n]*(?:\n(?!\n)[^\n]*)*)', text_response)
        if steps_matches:
            sections["deployment_plan"] = {"steps": [match[1].strip() for match in steps_matches[:5]]}
        
        # Configuration
        config_match = re.search(r'(?i)(configuration|config|setup)[:.]?\s*([^\n]*(?:\n(?!\n)[^\n]*)*)', text_response)
        if config_match:
            sections["configuration_management"] = {"description": config_match.group(2).strip()}
        
        # Monitoring
        monitor_match = re.search(r'(?i)(monitor|alert|observability)[:.]?\s*([^\n]*(?:\n(?!\n)[^\n]*)*)', text_response)
        if monitor_match:
            sections["monitoring_configuration"] = {"description": monitor_match.group(2).strip()}
        
        return sections
    
    def _create_fallback_deployment(self, raw_response: str = None) -> Dict[str, Any]:
        """Create fallback deployment response when parsing fails."""
        
        return {
            "deployment_type": "fallback_production_deployment",
            "status": "completed_with_fallback",
            "deployment_overview": {
                "strategy": "blue_green_deployment",
                "target_environment": "production",
                "deployment_time": "45 minutes",
                "rollback_time": "5 minutes",
                "availability_target": "99.9%"
            },
            "deployment_plan": {
                "phases": [
                    {
                        "phase": "Pre-deployment",
                        "duration": "10 minutes",
                        "tasks": [
                            "Verify deployment package integrity",
                            "Validate environment configuration",
                            "Backup current production state",
                            "Notify stakeholders of deployment window"
                        ]
                    },
                    {
                        "phase": "Deployment",
                        "duration": "25 minutes", 
                        "tasks": [
                            "Deploy to blue environment",
                            "Execute database migrations",
                            "Perform health checks and validation",
                            "Switch traffic to blue environment"
                        ]
                    },
                    {
                        "phase": "Post-deployment",
                        "duration": "10 minutes",
                        "tasks": [
                            "Monitor system performance",
                            "Validate critical user journeys",
                            "Confirm monitoring and alerting",
                            "Document deployment completion"
                        ]
                    }
                ],
                "rollback_triggers": [
                    "Health check failures",
                    "Performance degradation >20%",
                    "Error rate increase >5%",
                    "Critical functionality failures"
                ]
            },
            "infrastructure_configuration": {
                "platform": "cloud_provider",
                "compute": {
                    "instance_type": "medium",
                    "min_instances": 2,
                    "max_instances": 10,
                    "auto_scaling": "enabled"
                },
                "networking": {
                    "load_balancer": "application_load_balancer",
                    "ssl_termination": "enabled",
                    "cdn": "cloudflare",
                    "vpc": "dedicated_vpc"
                },
                "storage": {
                    "database": "managed_postgresql",
                    "file_storage": "object_storage", 
                    "backup_retention": "30_days"
                }
            },
            "environment_configurations": [
                {
                    "name": "production",
                    "variables": {
                        "NODE_ENV": "production",
                        "LOG_LEVEL": "info",
                        "DATABASE_POOL_SIZE": "20",
                        "CACHE_TTL": "3600"
                    },
                    "secrets": {
                        "DATABASE_URL": "encrypted",
                        "JWT_SECRET": "encrypted",
                        "API_KEYS": "encrypted"
                    }
                }
            ],
            "cicd_pipeline": {
                "triggers": [
                    "main branch commits",
                    "release tag creation",
                    "manual deployment approval"
                ],
                "stages": [
                    {
                        "name": "build",
                        "tasks": ["compile", "test", "security_scan", "package"]
                    },
                    {
                        "name": "staging_deploy",
                        "tasks": ["deploy_staging", "integration_tests", "performance_tests"]
                    },
                    {
                        "name": "production_deploy",
                        "tasks": ["manual_approval", "deploy_production", "smoke_tests"]
                    }
                ],
                "quality_gates": [
                    "unit_test_coverage > 80%",
                    "integration_tests passing",
                    "security_scan clean",
                    "performance_baseline_met"
                ]
            },
            "application_deployment": {
                "packaging": {
                    "format": "docker_container",
                    "registry": "container_registry",
                    "versioning": "semantic_versioning"
                },
                "deployment_strategy": {
                    "type": "blue_green",
                    "health_check_timeout": "300_seconds",
                    "deployment_timeout": "1800_seconds"
                },
                "configuration": {
                    "environment_variables": "injected_at_runtime",
                    "secrets_management": "vault_integration",
                    "feature_flags": "enabled"
                }
            },
            "database_deployment": {
                "migrations": {
                    "strategy": "forward_only",
                    "rollback_support": "limited",
                    "timeout": "600_seconds"
                },
                "backup": {
                    "pre_migration_backup": "required",
                    "retention": "7_days",
                    "verification": "automated"
                },
                "connection_management": {
                    "pool_size": "20",
                    "connection_timeout": "30_seconds",
                    "idle_timeout": "300_seconds"
                }
            },
            "configuration_management": {
                "secrets": {
                    "provider": "aws_secrets_manager",
                    "rotation": "automatic",
                    "encryption": "kms"
                },
                "environment_config": {
                    "source": "environment_variables",
                    "validation": "startup_validation",
                    "hot_reload": "disabled_in_production"
                },
                "feature_flags": {
                    "provider": "launchdarkly",
                    "rollout_strategy": "gradual",
                    "killswitch": "enabled"
                }
            },
            "monitoring_configuration": {
                "application_monitoring": {
                    "apm": "datadog",
                    "metrics": ["response_time", "throughput", "error_rate"],
                    "alerting": "pagerduty_integration"
                },
                "infrastructure_monitoring": {
                    "provider": "cloudwatch",
                    "metrics": ["cpu", "memory", "disk", "network"],
                    "dashboards": "grafana"
                },
                "logging": {
                    "aggregation": "elasticsearch",
                    "retention": "90_days",
                    "structured_logging": "enabled"
                },
                "uptime_monitoring": {
                    "provider": "pingdom",
                    "check_frequency": "1_minute",
                    "locations": "global"
                }
            },
            "security_configuration": {
                "authentication": {
                    "provider": "auth0",
                    "mfa": "required",
                    "session_timeout": "8_hours"
                },
                "network_security": {
                    "waf": "enabled",
                    "ddos_protection": "enabled",
                    "ssl_rating": "A+"
                },
                "data_protection": {
                    "encryption_at_rest": "aes_256",
                    "encryption_in_transit": "tls_1_3",
                    "key_management": "hsm"
                },
                "vulnerability_management": {
                    "scanning": "automated",
                    "frequency": "daily",
                    "remediation_sla": "critical_24h_high_72h"
                }
            },
            "backup_configuration": {
                "database_backup": {
                    "frequency": "daily",
                    "retention": "30_days",
                    "point_in_time_recovery": "enabled"
                },
                "application_backup": {
                    "configuration_backup": "daily",
                    "artifact_backup": "weekly",
                    "disaster_recovery": "cross_region"
                },
                "testing": {
                    "backup_verification": "weekly",
                    "restore_testing": "monthly",
                    "rto": "4_hours",
                    "rpo": "15_minutes"
                }
            },
            "health_checks": {
                "application_health": {
                    "endpoint": "/health",
                    "timeout": "5_seconds",
                    "frequency": "30_seconds"
                },
                "database_health": {
                    "connection_check": "enabled",
                    "query_performance": "monitored",
                    "replication_lag": "tracked"
                },
                "dependency_health": {
                    "external_services": "monitored",
                    "circuit_breakers": "enabled",
                    "fallback_strategies": "implemented"
                }
            },
            "performance_validation": {
                "baseline_metrics": {
                    "response_time_p95": "200ms",
                    "throughput": "1000_rps",
                    "error_rate": "<0.1%"
                },
                "load_testing": {
                    "frequency": "pre_deployment",
                    "duration": "30_minutes",
                    "user_scenarios": "critical_paths"
                },
                "capacity_planning": {
                    "growth_projection": "25%_quarterly",
                    "scaling_thresholds": "80%_utilization",
                    "resource_monitoring": "continuous"
                }
            },
            "rollback_procedures": {
                "triggers": [
                    "Health check failures > 2 minutes",
                    "Error rate > 5% for 1 minute",
                    "Response time > 500ms p95 for 2 minutes",
                    "Manual trigger by ops team"
                ],
                "process": [
                    "Stop traffic to new deployment",
                    "Route traffic back to previous version",
                    "Verify system stability",
                    "Investigate and document issues"
                ],
                "estimated_time": "5_minutes",
                "communication": "automated_alerts_and_notifications"
            },
            "operational_procedures": {
                "deployment_checklist": [
                    "Verify all tests passing",
                    "Check deployment window schedule",
                    "Confirm stakeholder notification",
                    "Validate rollback procedures",
                    "Execute deployment plan",
                    "Monitor post-deployment metrics"
                ],
                "incident_response": {
                    "severity_levels": ["P0", "P1", "P2", "P3"],
                    "escalation_paths": "defined",
                    "communication_channels": "slack_and_pagerduty"
                },
                "maintenance_windows": {
                    "frequency": "monthly",
                    "duration": "2_hours",
                    "notification": "72_hours_advance"
                }
            },
            "incident_response": {
                "detection": {
                    "automated_alerting": "enabled",
                    "escalation_rules": "defined",
                    "on_call_rotation": "24_7"
                },
                "response": {
                    "incident_commander": "designated",
                    "communication_channels": "war_room",
                    "status_page": "automated_updates"
                },
                "resolution": {
                    "runbooks": "comprehensive",
                    "escalation_paths": "defined",
                    "post_mortem": "required"
                }
            },
            "documentation": {
                "deployment_guide": "comprehensive_runbook",
                "troubleshooting_guide": "common_issues_and_solutions",
                "api_documentation": "openapi_specification",
                "operational_runbook": "incident_response_procedures"
            },
            "deployment_artifacts": [
                {
                    "name": "application_package",
                    "type": "docker_image",
                    "version": "v1.0.0",
                    "registry": "production_registry"
                },
                {
                    "name": "database_migrations",
                    "type": "sql_scripts",
                    "version": "v1.0.0",
                    "validation": "tested"
                },
                {
                    "name": "configuration_files",
                    "type": "yaml_configs",
                    "version": "v1.0.0",
                    "encryption": "secrets_encrypted"
                }
            ],
            "post_deployment_tasks": [
                "Monitor system metrics for 2 hours",
                "Validate critical user journeys",
                "Check error rates and performance",
                "Update deployment status dashboard",
                "Send deployment completion notification"
            ],
            "maintenance_procedures": {
                "regular_maintenance": {
                    "frequency": "weekly",
                    "tasks": ["log_rotation", "cache_cleanup", "metric_aggregation"]
                },
                "security_updates": {
                    "frequency": "monthly",
                    "process": "automated_with_approval",
                    "testing": "staging_environment"
                },
                "capacity_review": {
                    "frequency": "quarterly",
                    "metrics": ["growth_trends", "resource_utilization"],
                    "planning": "6_month_horizon"
                }
            },
            "scaling_configuration": {
                "horizontal_scaling": {
                    "trigger": "cpu_80%_or_memory_85%",
                    "cooldown": "5_minutes",
                    "max_instances": "20"
                },
                "vertical_scaling": {
                    "database": "automated_scaling",
                    "cache": "redis_cluster",
                    "storage": "auto_expanding"
                }
            },
            "cost_optimization": {
                "resource_scheduling": "non_prod_shutdown",
                "reserved_instances": "production_workloads",
                "monitoring": "cost_alerts_enabled",
                "optimization": "quarterly_review"
            },
            "compliance_validation": {
                "security_compliance": "soc2_type2",
                "data_protection": "gdpr_compliant",
                "audit_logging": "comprehensive",
                "access_controls": "principle_of_least_privilege"
            },
            "deployment_success_rate": 0.95,
            "operational_readiness": 0.9,
            "fallback_reason": "Deployment response parsing failed",
            "original_response": raw_response[:300] + "..." if raw_response and len(raw_response) > 300 else raw_response
        }
    
    def _create_orchestrator_handoff_instructions(self, context: List[ContextArtifact]) -> str:
        """Create specific instructions for handoff to Orchestrator for project completion."""
        
        instructions = """Based on the completed deployment, finalize project delivery and operational handoff.

Your project completion approach should include:

1. **Project Delivery Summary**
   - Compile comprehensive project delivery documentation
   - Summarize all phases completed (Discovery → Plan → Design → Build → Validate → Launch)
   - Document final deliverables and their locations
   - Create project success metrics and achievement summary

2. **Operational Handoff**
   - Transfer operational procedures and documentation to support teams
   - Provide monitoring and alerting configuration details
   - Document incident response and escalation procedures
   - Create operational runbooks and troubleshooting guides

3. **Stakeholder Communication**
   - Prepare project completion report for stakeholders
   - Document lessons learned and best practices
   - Create recommendations for future improvements
   - Schedule project retrospective and knowledge transfer

4. **System Documentation**
   - Ensure all technical documentation is complete and accessible
   - Verify deployment procedures and rollback plans are documented
   - Confirm monitoring and maintenance procedures are established
   - Validate backup and disaster recovery procedures

Please ensure complete project closure with proper knowledge transfer and operational readiness."""
        
        if context:
            deployment_details = self._extract_deployment_details(context)
            instructions += f"\n\nDEPLOYMENT COMPLETION DETAILS:\n{deployment_details}"
        
        return instructions
    
    def _extract_deployment_details(self, context: List[ContextArtifact]) -> str:
        """Extract key deployment details from context for handoff instructions."""
        
        deployment_details = []
        
        for artifact in context:
            if isinstance(artifact.content, dict):
                # Extract deployment status
                status = artifact.content.get("status", "unknown")
                if status == "completed":
                    deployment_details.append("- Deployment completed successfully")
                
                # Extract monitoring configuration
                monitoring = artifact.content.get("monitoring_configuration", {})
                if monitoring:
                    deployment_details.append("- Monitoring and alerting configured")
                
                # Extract operational readiness
                readiness = artifact.content.get("operational_readiness", 0)
                if readiness > 0.8:
                    deployment_details.append(f"- System operational readiness: {readiness:.2f}")
        
        if not deployment_details:
            return "- Review deployment artifacts for completion status"
        
        return "\n".join(deployment_details[:5])  # Limit to 5 items
    
    def _create_deployment_summary(self, context: List[ContextArtifact]) -> str:
        """Create summary of deployment for handoff metadata."""
        
        if not context:
            return "No deployment context available"
        
        summary_parts = []
        for artifact in context:
            if isinstance(artifact.content, dict):
                strategy = artifact.content.get("deployment_overview", {}).get("strategy", "unknown")
                environments = len(artifact.content.get("environment_configurations", []))
                summary_parts.append(f"strategy:{strategy},environments:{environments}")
            else:
                summary_parts.append("deployment configuration")
        
        return ", ".join(summary_parts) if summary_parts else "basic deployment setup"
    
    def _extract_operational_status(self, context: List[ContextArtifact]) -> str:
        """Extract operational status from context."""
        
        for artifact in context:
            if isinstance(artifact.content, dict):
                readiness = artifact.content.get("operational_readiness", 0)
                if readiness > 0.9:
                    return "fully_operational"
                elif readiness > 0.7:
                    return "operational"
                elif readiness > 0.5:
                    return "partially_operational"
        
        return "unknown"
    
    def _check_monitoring_status(self, context: List[ContextArtifact]) -> bool:
        """Check if monitoring is properly configured based on context."""

        for artifact in context:
            if isinstance(artifact.content, dict):
                monitoring = artifact.content.get("monitoring_configuration", {})
                if monitoring and len(monitoring) > 0:
                    return True

        return False

    def _validate_deployment_completeness(self, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Validate completeness of deployment and identify gaps.

        Args:
            context: Context artifacts to analyze

        Returns:
            Completeness validation results
        """
        missing_elements = []
        confidence_score = 1.0
        requires_clarification = False

        # Check for testing context
        testing_found = any(
            artifact.artifact_type in ["quality_testing", "testing_document"] or
            (isinstance(artifact.content, dict) and artifact.content.get("testing_type") == "comprehensive_quality_assurance")
            for artifact in context
        )

        if not testing_found:
            missing_elements.append("testing_context")
            confidence_score -= 0.4
            requires_clarification = True

        # Check for implementation context
        implementation_found = any(
            artifact.artifact_type in ["code_implementation", "implementation_design"] or
            (isinstance(artifact.content, dict) and artifact.content.get("implementation_type") == "full_stack_implementation")
            for artifact in context
        )

        if not implementation_found:
            missing_elements.append("implementation_context")
            confidence_score -= 0.3
            requires_clarification = True

        # Check for existing deployment artifacts
        existing_deployment = [
            artifact for artifact in context
            if isinstance(artifact.content, dict) and
            artifact.content.get("deployment_type") == "production_deployment_automation"
        ]

        if not existing_deployment:
            missing_elements.append("deployment_design")
            confidence_score -= 0.5
            requires_clarification = True

        # Check for specific deployment elements
        if existing_deployment:
            latest_deployment = existing_deployment[-1].content

            # Check infrastructure configuration
            infrastructure = latest_deployment.get("infrastructure_configuration", {})
            if not infrastructure:
                missing_elements.append("infrastructure_configuration")
                confidence_score -= 0.2

            # Check monitoring configuration
            monitoring = latest_deployment.get("monitoring_configuration", {})
            if not monitoring:
                missing_elements.append("monitoring_configuration")
                confidence_score -= 0.2

            # Check security configuration
            security = latest_deployment.get("security_configuration", {})
            if not security:
                missing_elements.append("security_configuration")
                confidence_score -= 0.1

            # Check rollback procedures
            rollback = latest_deployment.get("rollback_procedures", {})
            if not rollback:
                missing_elements.append("rollback_procedures")
                confidence_score -= 0.1

        # Determine if clarification is needed
        if confidence_score < 0.6 or len(missing_elements) > 3:
            requires_clarification = True

        return {
            "is_complete": len(missing_elements) == 0,
            "confidence_score": max(0.0, confidence_score),
            "missing_elements": missing_elements,
            "requires_clarification": requires_clarification,
            "existing_deployment_count": len(existing_deployment),
            "recommendations": self._generate_deployment_recommendations(missing_elements)
        }

    def _generate_deployment_recommendations(self, missing_elements: List[str]) -> List[str]:
        """Generate recommendations for addressing deployment gaps."""
        recommendations = []

        for element in missing_elements:
            if element == "testing_context":
                recommendations.append("Gather comprehensive testing results before deployment")
            elif element == "implementation_context":
                recommendations.append("Obtain detailed implementation artifacts")
            elif element == "deployment_design":
                recommendations.append("Conduct deployment planning session")
            elif element == "infrastructure_configuration":
                recommendations.append("Configure target infrastructure and environment")
            elif element == "monitoring_configuration":
                recommendations.append("Set up monitoring and alerting systems")
            elif element == "security_configuration":
                recommendations.append("Configure security controls and compliance")
            elif element == "rollback_procedures":
                recommendations.append("Define rollback and disaster recovery procedures")

        return recommendations

    def _generate_deployment_clarification_requests(self, task: Task, missing_elements: List[str]) -> List[Dict[str, Any]]:
        """Generate HITL requests for deployment clarification.

        Args:
            task: Current task
            missing_elements: List of missing deployment elements

        Returns:
            List of HITL request configurations
        """
        hitl_requests = []

        for element in missing_elements:
            if element == "testing_context":
                hitl_requests.append({
                    "question": "Please provide the testing results and quality assessment for deployment",
                    "options": ["Share testing report", "Provide quality metrics", "Specify deployment readiness criteria"],
                    "priority": "high",
                    "reason": "Missing testing context for deployment"
                })

            elif element == "implementation_context":
                hitl_requests.append({
                    "question": "What are the implementation details and deployment requirements?",
                    "options": ["Share implementation artifacts", "Specify deployment environment", "Provide infrastructure requirements"],
                    "priority": "high",
                    "reason": "Implementation context required for deployment"
                })

            elif element == "infrastructure_configuration":
                hitl_requests.append({
                    "question": "What is the target deployment environment and infrastructure requirements?",
                    "options": ["Specify cloud provider", "Define infrastructure requirements", "Provide environment access"],
                    "priority": "medium",
                    "reason": "Infrastructure configuration needed"
                })

            elif element == "monitoring_configuration":
                hitl_requests.append({
                    "question": "What monitoring and alerting requirements should be implemented?",
                    "options": ["Specify monitoring tools", "Define alerting thresholds", "Provide operational requirements"],
                    "priority": "medium",
                    "reason": "Monitoring configuration required"
                })

        return hitl_requests

    def _prepare_enhanced_deployment_context(self, task: Task, context: List[ContextArtifact],
                                           completeness_check: Dict[str, Any]) -> str:
        """Prepare enhanced deployment context with completeness information."""

        base_context = self._prepare_deployment_context(task, context)

        # Add completeness information
        completeness_info = [
            "",
            "DEPLOYMENT COMPLETENESS STATUS:",
            f"Confidence Score: {completeness_check.get('confidence_score', 0):.2f}",
            f"Missing Elements: {', '.join(completeness_check.get('missing_elements', [])) or 'None'}",
            f"Requires Clarification: {completeness_check.get('requires_clarification', False)}",
        ]

        if completeness_check.get("recommendations"):
            completeness_info.extend([
                "",
                "DEPLOYMENT RECOMMENDATIONS:",
                *[f"- {rec}" for rec in completeness_check["recommendations"][:3]]
            ])

        completeness_info.extend([
            "",
            "ENHANCED DEPLOYMENT REQUIREMENTS:",
            "Focus on addressing the identified gaps while maintaining deployment quality.",
            "Generate specific clarification questions for technical stakeholders if needed.",
            "Ensure comprehensive coverage of infrastructure, security, and operational requirements.",
            "Provide actionable recommendations for production readiness."
        ])

        return base_context + "\n".join(completeness_info)

    async def _generate_deployment_from_template(self, deployment_result: Dict[str, Any], task: Task,
                                               context: List[ContextArtifact]) -> Optional[Dict[str, Any]]:
        """Generate professional deployment plan using BMAD templates.

        Args:
            deployment_result: Structured deployment results
            task: Current task
            context: Context artifacts

        Returns:
            Generated deployment document or None if template service unavailable
        """
        if not self.template_service:
            logger.warning("Template service not available, skipping deployment document generation")
            return None

        try:
            # Prepare template variables
            template_vars = {
                "project_id": str(task.project_id),
                "task_id": str(task.task_id),
                "deployment_date": datetime.now(timezone.utc).isoformat(),
                "deployment_overview": deployment_result.get("deployment_overview", {}),
                "deployment_plan": deployment_result.get("deployment_plan", {}),
                "infrastructure_configuration": deployment_result.get("infrastructure_configuration", {}),
                "environment_configurations": deployment_result.get("environment_configurations", []),
                "cicd_pipeline": deployment_result.get("cicd_pipeline", {}),
                "application_deployment": deployment_result.get("application_deployment", {}),
                "database_deployment": deployment_result.get("database_deployment", {}),
                "configuration_management": deployment_result.get("configuration_management", {}),
                "monitoring_configuration": deployment_result.get("monitoring_configuration", {}),
                "security_configuration": deployment_result.get("security_configuration", {}),
                "backup_configuration": deployment_result.get("backup_configuration", {}),
                "health_checks": deployment_result.get("health_checks", {}),
                "performance_validation": deployment_result.get("performance_validation", {}),
                "rollback_procedures": deployment_result.get("rollback_procedures", {}),
                "operational_procedures": deployment_result.get("operational_procedures", {}),
                "incident_response": deployment_result.get("incident_response", {}),
                "documentation": deployment_result.get("documentation", {}),
                "deployment_artifacts": deployment_result.get("deployment_artifacts", []),
                "post_deployment_tasks": deployment_result.get("post_deployment_tasks", []),
                "maintenance_procedures": deployment_result.get("maintenance_procedures", {}),
                "scaling_configuration": deployment_result.get("scaling_configuration", {}),
                "cost_optimization": deployment_result.get("cost_optimization", {}),
                "compliance_validation": deployment_result.get("compliance_validation", {}),
                "deployment_success_rate": deployment_result.get("deployment_success_rate", 0.95),
                "operational_readiness": deployment_result.get("operational_readiness", 0.9)
            }

            # Generate deployment document using template
            deployment_content = await self.template_service.render_template_async(
                template_name="deployment-tmpl.yaml",
                variables=template_vars
            )

            logger.info("Deployment document generated from template",
                       template="deployment-tmpl.yaml",
                       content_length=len(str(deployment_content)))

            return {
                "document_type": "comprehensive_deployment_document",
                "template_used": "deployment-tmpl.yaml",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "content": deployment_content,
                "metadata": {
                    "deployment_success_rate": template_vars["deployment_success_rate"],
                    "operational_readiness": template_vars["operational_readiness"],
                    "environments_configured": len(template_vars["environment_configurations"]),
                    "monitoring_configured": bool(template_vars["monitoring_configuration"])
                }
            }

        except Exception as e:
            logger.error("Failed to generate deployment document from template",
                        error=str(e),
                        template="deployment-tmpl.yaml")
            return None

    def _create_deployment_artifacts(self, deployment_result: Dict[str, Any],
                                   deployment_document: Optional[Dict[str, Any]], task: Task) -> List[str]:
        """Create context artifacts for deployment results.

        Args:
            deployment_result: Structured deployment results
            deployment_document: Generated deployment document
            task: Current task

        Returns:
            List of created artifact IDs
        """
        if not self.context_store:
            logger.warning("Context store not available, skipping artifact creation")
            return []

        created_artifacts = []

        try:
            # Create deployment artifact
            deployment_artifact = self.context_store.create_artifact(
                project_id=task.project_id,
                source_agent=self.agent_type.value,
                artifact_type="deployment_configuration",
                content=deployment_result
            )
            created_artifacts.append(str(deployment_artifact.context_id))

            # Create deployment document artifact if available
            if deployment_document:
                document_artifact = self.context_store.create_artifact(
                    project_id=task.project_id,
                    source_agent=self.agent_type.value,
                    artifact_type="deployment_document",
                    content=deployment_document
                )
                created_artifacts.append(str(document_artifact.context_id))

            logger.info("Deployment artifacts created",
                       deployment_artifact=str(deployment_artifact.context_id),
                       document_artifact=created_artifacts[1] if len(created_artifacts) > 1 else None)

        except Exception as e:
            logger.error("Failed to create deployment artifacts",
                        error=str(e),
                        task_id=str(task.task_id))

        return created_artifacts

    def _validate_final_deployment(self, deployment_result: Dict[str, Any],
                                 deployment_document: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform final validation of deployment completeness and quality.

        Args:
            deployment_result: Structured deployment results
            deployment_document: Generated deployment document

        Returns:
            Final validation results
        """
        validation_results = {
            "overall_quality": "good",
            "issues_found": [],
            "recommendations": [],
            "ready_for_production": True
        }

        # Check deployment completeness
        success_rate = deployment_result.get("deployment_success_rate", 0.95)
        operational_readiness = deployment_result.get("operational_readiness", 0.9)
        environments = len(deployment_result.get("environment_configurations", []))
        monitoring = deployment_result.get("monitoring_configuration", {})

        if success_rate < 0.9:
            validation_results["issues_found"].append("Low deployment success rate")
            validation_results["recommendations"].append("Improve deployment reliability")
            validation_results["overall_quality"] = "needs_review"

        if operational_readiness < 0.8:
            validation_results["issues_found"].append("Low operational readiness")
            validation_results["recommendations"].append("Enhance operational procedures")
            validation_results["overall_quality"] = "needs_improvement"

        if environments < 1:
            validation_results["issues_found"].append("No environment configurations")
            validation_results["recommendations"].append("Configure deployment environments")
            validation_results["overall_quality"] = "needs_improvement"

        if not monitoring:
            validation_results["issues_found"].append("Monitoring not configured")
            validation_results["recommendations"].append("Set up monitoring and alerting")
            validation_results["ready_for_production"] = False

        # Check rollback procedures
        rollback = deployment_result.get("rollback_procedures", {})
        if not rollback:
            validation_results["issues_found"].append("Rollback procedures missing")
            validation_results["recommendations"].append("Define rollback and recovery procedures")
            validation_results["ready_for_production"] = False

        # Check security configuration
        security = deployment_result.get("security_configuration", {})
        if not security:
            validation_results["issues_found"].append("Security configuration incomplete")
            validation_results["recommendations"].append("Configure security controls")
            validation_results["ready_for_production"] = False

        # Check deployment document generation
        if not deployment_document:
            validation_results["issues_found"].append("Deployment document generation failed")
            validation_results["recommendations"].append("Manual deployment documentation recommended")

        # Determine overall readiness
        if validation_results["issues_found"] and validation_results["ready_for_production"]:
            validation_results["ready_for_production"] = False

        logger.info("Final deployment validation completed",
                   quality=validation_results["overall_quality"],
                   issues=len(validation_results["issues_found"]),
                   ready=validation_results["ready_for_production"])

        return validation_results
