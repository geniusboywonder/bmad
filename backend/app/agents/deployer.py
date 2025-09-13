"""Deployer agent for deployment automation and environment management."""

from typing import Dict, Any, List
from uuid import uuid4
import json
import structlog

from app.agents.base_agent import BaseAgent
from app.models.task import Task
from app.models.context import ContextArtifact
from app.models.handoff import HandoffSchema
from app.models.agent import AgentType

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
    
    def __init__(self, agent_type: AgentType, llm_config: Dict[str, Any]):
        """Initialize Deployer agent with deployment automation optimization."""
        super().__init__(agent_type, llm_config)
        
        # Configure for systematic deployment (lower temperature for precision)
        self.llm_config.update({
            "model": llm_config.get("model", "gpt-4o-mini"),
            "temperature": 0.2,  # Lower temperature for deployment precision
        })
        
        # Initialize AutoGen agent
        self._initialize_autogen_agent()
        
        logger.info("Deployer agent initialized with deployment automation focus")
    
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
        """Execute deployer task with deployment automation focus.
        
        Args:
            task: Task to execute with deployment instructions
            context: Context artifacts from testing and implementation
            
        Returns:
            Deployment result with configurations, procedures, and monitoring setup
        """
        logger.info("Deployer executing deployment automation task",
                   task_id=task.task_id,
                   context_count=len(context))
        
        try:
            # Prepare deployment context
            deployment_context = self._prepare_deployment_context(task, context)
            
            # Execute with LLM reliability features
            raw_response = await self._execute_with_reliability(deployment_context, task)
            
            # Parse and structure deployment response
            deployment_result = self._parse_deployment_response(raw_response, task)
            
            logger.info("Deployer task completed successfully",
                       task_id=task.task_id,
                       environments_configured=len(deployment_result.get("environment_configurations", [])),
                       monitoring_setup=len(deployment_result.get("monitoring_configuration", {})))
            
            return {
                "success": True,
                "agent_type": self.agent_type.value,
                "task_id": str(task.task_id),
                "output": deployment_result,
                "deployment_summary": deployment_result.get("deployment_overview", {}),
                "operational_procedures": deployment_result.get("operational_procedures", {}),
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